const express = require("express");
const axios = require("axios");

const app = express();
app.use(express.json());

const statUrl = process.env.STAT_URL || "http://stat:8001";

const validTokens = ["demo-token"];

function authMiddleware(req, res, next) {
  const token = req.headers["authorization"]?.replace("Bearer ", "");
  if (!validTokens.includes(token)) {
    return res.status(401).json({ error: "Unauthorized" });
  }
  next();
}

app.get("/health", (req, res) => {
  res.json({ status: "ok", service: "gateway", port: process.env.PORT || 8000 });
});

app.post("/api/dashboard", authMiddleware, async (req, res) => {
  const {
    keywords = [],
    exclude = [],
    dateRange = [],
    limit = 10,
  } = req.body;

  let fromDate = "";
  let toDate = "";
  if (dateRange && dateRange.length === 2) {
    fromDate = dateRange[0];
    toDate = dateRange[1];
  }

  const statReqBody = {
    include_keywords: keywords,
    exclude_keywords: exclude,
    from_date: fromDate,
    to_date: toDate,
    example_limit: limit,
  };

  let stats;
  try {
    const statResp = await axios.post(${statUrl}/stats, statReqBody);
    stats = statResp.data;
  } catch (err) {
    console.error("Stat service error:", err.message);
    return res.status(500).json({ error: "Failed to fetch stats" });
  }

  const posts = stats.example_posts || [];
  const mentionCount = stats.mention_count || 0;
  const sampleSize = Math.min(limit, posts.length);

  // NO MORE NLP CALLS
  // Stats already aggregated sentiments via SQL using the new Go endpoint
  // And example_posts already holds .sentiment and .sentiment_score 

  try {
    return res.json({
      sentimentPercentage: stats.sentiment_percentage || { positive: 0, neutral: 0, negative: 0 },
      topKeywords: stats.top_keywords || [],
      trends: stats.trends || [],
      examplePosts: posts.slice(0, sampleSize),
      mentionCount: mentionCount,
      totalAnalyzedPosts: mentionCount,
    });
  } catch (err) {
    console.error("Error building response:", err);
    return res.status(500).json({ error: "Failed to build dashboard response" });
  }
});

const port = process.env.PORT || 8000;
app.listen(port, () => {
  console.log(Gateway listening on port );
});