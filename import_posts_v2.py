import argparse
import csv
import re
import sqlite3
import subprocess
import sys
from pathlib import Path
import json

try:
    import joblib
    HAS_NLP = True
except ImportError:
    HAS_NLP = False

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="./data/listenai.db")
    parser.add_argument("--csv", default="./data/posts.csv")
    parser.add_argument("--platform", default="x")
    return parser.parse_args()

def init_db(conn):
    conn.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            author TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            sentiment TEXT NOT NULL DEFAULT 'neutral',
            sentiment_score REAL NOT NULL DEFAULT 0.0
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS post_tokens (
            post_id INTEGER,
            token TEXT,
            FOREIGN KEY(post_id) REFERENCES posts(id)
        )
    ''')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_sentiment ON posts(sentiment)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_token ON post_tokens(token)')

def import_posts(db_path, csv_path, platform):
    vectorizer = None
    classifier = None
    if HAS_NLP:
        try:
            vectorizer = joblib.load('nlp/tfidf_vectorizer.pkl')
            classifier = joblib.load('nlp/svm_model.pkl')
        except Exception as e:
            print(f"Warning: NLP models not loaded: {e}")

    conn = sqlite3.connect(db_path)
    init_db(conn)
    inserted = 0
    skipped = 0

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        with conn:
            for row in reader:
                author = (row.get("name") or "").strip()
                date_str = (row.get("date") or "").strip()
                content = (row.get("content") or "").strip()

                if not author or not content:
                    continue

                created_at = f"{date_str}T00:00:00Z"
                
                # NLP Prediction
                sentiment = 'neutral'
                score = 0.0
                if classifier and vectorizer:
                    try:
                        X = vectorizer.transform([content])
                        sentiment = classifier.predict(X)[0]
                        score = 1.0
                    except:
                        pass

                exists = conn.execute("SELECT 1 FROM posts WHERE author = ? AND content = ? AND created_at = ?", (author, content, created_at)).fetchone()
                if exists:
                    skipped += 1
                    continue

                cur = conn.execute(
                    "INSERT INTO posts(platform, author, content, created_at, sentiment, sentiment_score) VALUES(?, ?, ?, ?, ?, ?)",
                    (platform, author, content, created_at, sentiment, score)
                )
                post_id = cur.lastrowid
                
                # Tokenize and insert for inverted index
                tokens = [w for w in re.findall(r"[a-zA-Z']+|[\u4e00-\u9fff]+", content.lower()) if len(w) > 1]
                conn.executemany("INSERT INTO post_tokens(post_id, token) VALUES(?, ?)", [(post_id, t) for t in tokens])
                inserted += 1

    total = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    conn.close()
    return {"inserted": inserted, "skipped": skipped, "total": total}

def main():
    args = parse_args()
    db_path = Path(args.db).resolve()
    csv_path = Path(args.csv).resolve()
    print(import_posts(db_path, csv_path, args.platform))

if __name__ == "__main__":
    main()