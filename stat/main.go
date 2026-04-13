package main

import (
    "database/sql"
    "encoding/json"
    "fmt"
    "log"
    "net/http"
    "os"
    "strings"
    "time"

    _ "modernc.org/sqlite"
)

type Post struct {
    ID             int     \json:"id"\
    Platform       string  \json:"platform"\
    Author         string  \json:"author"\
    Content        string  \json:"content"\
    CreatedAt      string  \json:"created_at"\
    Sentiment      string  \json:"sentiment"\
    SentimentScore float64 \json:"sentiment_score"\
}

type StatsRequest struct {
    IncludeKeywords []string \json:"include_keywords"\
    ExcludeKeywords []string \json:"exclude_keywords"\
    FromDate        string   \json:"from_date"\
    ToDate          string   \json:"to_date"\
    ExampleLimit    int      \json:"example_limit"\
    PostLimit       int      \json:"post_limit"\
}

type KeywordCount struct {
    Keyword string \json:"keyword"\
    Count   int    \json:"count"\
}

type TrendPoint struct {
    Date  string \json:"date"\
    Count int    \json:"count"\
}

type StatsResponse struct {
    MentionCount        int               \json:"mention_count"\
    TopKeywords         []KeywordCount    \json:"top_keywords"\
    Trends              []TrendPoint      \json:"trends"\
    SentimentPercentage map[string]float64\json:"sentiment_percentage"\
    ExamplePosts        []Post            \json:"example_posts"\
    Posts               []Post            \json:"posts"\ // Kept for backwards compatibility but we limit it
}

var stopWords = map[string]bool{
    "the": true, "a": true, "an": true, "and": true, "or": true, "to": true,
    "of": true, "in": true, "on": true, "for": true, "with": true, "is": true,
    "are": true, "it": true, "this": true, "that": true, "my": true, "our": true,
    "your": true, "but": true, "from": true, "at": true, "was": true,
    "的": true, "了": true, "是": true, "我": true, "你": true, "他": true, "在": true, "就": true,
    "有": true, "也": true, "都": true, "不": true, "而": true, "這": true, "那": true, "呢": true,
    "啊": true, "喔": true, "嗎": true, "吧": true, "與": true, "和": true, "或": true,
}

func parseDateRange(fromDate, toDate string) (string, string, error) {
    layout := "2006-01-02"
    now := time.Now()

    if fromDate == "" {
        fromDate = now.AddDate(0, 0, -30).Format(layout)
    }
    if toDate == "" {
        toDate = now.Format(layout)
    }

    if _, err := time.Parse(layout, fromDate); err != nil {
        return "", "", fmt.Errorf("invalid from_date: %w", err)
    }
    if _, err := time.Parse(layout, toDate); err != nil {
        return "", "", fmt.Errorf("invalid to_date: %w", err)
    }

    return fromDate, toDate, nil
}

func fetchStats(db *sql.DB, req StatsRequest) (*StatsResponse, error) {
    fd, td, err := parseDateRange(req.FromDate, req.ToDate)
    if err != nil {
        return nil, err
    }

    // Build WHERE clause
    whereParams := []interface{}{fd, td + "T23:59:59Z"}
    whereSql := "created_at >= ? AND created_at <= ?"

    if len(req.IncludeKeywords) > 0 {
        var orClauses []string
        for _, k := range req.IncludeKeywords {
            orClauses = append(orClauses, "content LIKE ?")
            whereParams = append(whereParams, "%"+k+"%")
        }
        whereSql += " AND (" + strings.Join(orClauses, " OR ") + ")"
    }

    if len(req.ExcludeKeywords) > 0 {
        for _, k := range req.ExcludeKeywords {
            whereSql += " AND content NOT LIKE ?"
            whereParams = append(whereParams, "%"+k+"%")
        }
    }

    // 1. Get Mention Count
    var count int
    err = db.QueryRow("SELECT COUNT(*) FROM posts WHERE "+whereSql, whereParams...).Scan(&count)
    if err != nil {
        return nil, err
    }

    // 2. Get example posts (to show in UI and compute everything fast)
    limit := req.ExampleLimit
    if limit <= 0 {
        limit = 500
    }
    rows, err := db.Query("SELECT id, platform, author, content, created_at, sentiment, sentiment_score FROM posts WHERE "+whereSql+" ORDER BY created_at DESC LIMIT ?", append(whereParams, limit)...)
    if err != nil {
        return nil, err
    }
    defer rows.Close()

    var posts []Post
    for rows.Next() {
        var p Post
        if err := rows.Scan(&p.ID, &p.Platform, &p.Author, &p.Content, &p.CreatedAt, &p.Sentiment, &p.SentimentScore); err != nil {
            return nil, err
        }
        posts = append(posts, p)
    }

    // 3. Setup trends & sentiments aggregation through SQL GROUP BY
    trendRows, err := db.Query("SELECT substr(created_at, 1, 10) as date_str, COUNT(*) FROM posts WHERE "+whereSql+" GROUP BY date_str ORDER BY date_str ASC", whereParams...)
    var trends []TrendPoint
    if err == nil {
        defer trendRows.Close()
        for trendRows.Next() {
            var tp TrendPoint
            trendRows.Scan(&tp.Date, &tp.Count)
            trends = append(trends, tp)
        }
    }

    sentimentRows, err := db.Query("SELECT sentiment, COUNT(*) as cnt FROM posts WHERE "+whereSql+" GROUP BY sentiment", whereParams...)
    sentimentMap := map[string]float64{"positive": 0, "neutral": 0, "negative": 0}
    if err == nil {
        defer sentimentRows.Close()
        for sentimentRows.Next() {
            var s string
            var c float64
            sentimentRows.Scan(&s, &c)
            sentimentMap[s] = c
        }
    }
    // Convert counts to percentage
    totalSentiments := sentimentMap["positive"] + sentimentMap["neutral"] + sentimentMap["negative"]
    if totalSentiments > 0 {
        sentimentMap["positive"] = float64(int((sentimentMap["positive"]/totalSentiments)*10000)) / 100
        sentimentMap["neutral"] = float64(int((sentimentMap["neutral"]/totalSentiments)*10000)) / 100
        sentimentMap["negative"] = float64(int((sentimentMap["negative"]/totalSentiments)*10000)) / 100
    }

    // 4. Get top keywords using inverted index (post_tokens) + JOIN
    var keywords []KeywordCount
    if count > 0 {
        topTokensSql := "SELECT pt.token, COUNT(pt.token) as cnt FROM post_tokens pt INNER JOIN posts p ON pt.post_id = p.id WHERE " + whereSql + " GROUP BY pt.token ORDER BY cnt DESC LIMIT 50"
        tokRows, err := db.Query(topTokensSql, whereParams...)
        if err == nil {
            defer tokRows.Close()
            for tokRows.Next() {
                var tk string
                var c int
                tokRows.Scan(&tk, &c)
                // Filter stop words and length and current keywords
                if stopWords[tk] || len([]rune(tk)) < 2 {
                    continue
                }
                
                // Skip if it's the search keyword itself
                skip := false
                for _, ik := range req.IncludeKeywords {
                    if strings.ToLower(tk) == strings.ToLower(ik) {
                        skip = true; break
                    }
                }
                if skip { continue }
                
                keywords = append(keywords, KeywordCount{Keyword: tk, Count: c})
                if len(keywords) == 10 {
                    break
                }
            }
        }
    }

    return &StatsResponse{
        MentionCount:        count,
        TopKeywords:         keywords,
        Trends:              trends,
        ExamplePosts:        posts,
        Posts:               posts,
        SentimentPercentage: sentimentMap,
    }, nil
}

func handleStats(db *sql.DB) http.HandlerFunc {
    return func(w http.ResponseWriter, r *http.Request) {
        if r.Method != http.MethodPost {
            http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
            return
        }

        var req StatsRequest
        if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
            http.Error(w, "Bad request body", http.StatusBadRequest)
            return
        }

        resp, err := fetchStats(db, req)
        if err != nil {
            log.Printf("fetchStats error: %v", err)
            http.Error(w, "Internal server error", http.StatusInternalServerError)
            return
        }

        w.Header().Set("Content-Type", "application/json")
        json.NewEncoder(w).Encode(resp)
    }
}

func handleHealth() http.HandlerFunc {
    return func(w http.ResponseWriter, r *http.Request) {
        port := os.Getenv("STAT_PORT")
        if port == "" {
            port = "8001"
        }
        res := map[string]string{
            "status":  "ok",
            "service": "stat",
            "port":    port,
        }
        w.Header().Set("Content-Type", "application/json")
        json.NewEncoder(w).Encode(res)
    }
}

func main() {
    dbPath := os.Getenv("SQLITE_PATH")
    if dbPath == "" {
        dbPath = "./data/listenai.db"
    }

    db, err := sql.Open("sqlite", dbPath)
    if err != nil {
        log.Fatalf("Failed to open db: %v", err)
    }
    defer db.Close()

    // Initialize missing schema safely
    _, err = db.Exec(\
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            author TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            sentiment TEXT NOT NULL DEFAULT 'neutral',
            sentiment_score REAL NOT NULL DEFAULT 0.0
        );
        CREATE TABLE IF NOT EXISTS post_tokens (
            post_id INTEGER,
            token TEXT,
            FOREIGN KEY(post_id) REFERENCES posts(id)
        );
        CREATE INDEX IF NOT EXISTS idx_sentiment ON posts(sentiment);
        CREATE INDEX IF NOT EXISTS idx_token ON post_tokens(token);
    \)
    if err != nil {
        log.Printf("Warning: Failed to init schema: %v", err)
    }

    http.HandleFunc("/stats", handleStats(db))
    http.HandleFunc("/health", handleHealth())

    port := os.Getenv("STAT_PORT")
    if port == "" {
        port = "8001"
    }
    addr := ":" + port
    log.Printf("Stat server listening on %s", addr)
    if err := http.ListenAndServe(addr, nil); err != nil {
        log.Fatalf("ListenAndServe error: %v", err)
    }
}