import os
from collections import Counter

from fastapi import FastAPI
from pydantic import BaseModel
import joblib

app = FastAPI(title="listen-ai-nlp")

# Load trained TF-IDF vectorizer and SVM model
try:
    vectorizer = joblib.load('tfidf_vectorizer.pkl')
    classifier = joblib.load('svm_model.pkl')
except Exception as e:
    print(f"Failed to load SVM model: {e}")
    vectorizer = None
    classifier = None

def classify_text(text: str) -> tuple[str, float]:
    if not text.strip():
        return "neutral", 0.0
        
    if classifier is None or vectorizer is None:
        return "neutral", 0.0

    X = vectorizer.transform([text])
    label = classifier.predict(X)[0]
    
    score = 1.0
    
    if label not in ['positive', 'negative', 'neutral']:
        label = 'neutral'
        
    return label, score


class SentimentRequest(BaseModel):
    texts: list[str]


class SentimentItem(BaseModel):
    text: str
    label: str
    score: float


class SentimentResponse(BaseModel):
    sentiment_percentage: dict[str, float]
    classifications: list[SentimentItem]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "nlp", "port": os.getenv("NLP_PORT", "8001")}


@app.post("/sentiment", response_model=SentimentResponse)
def sentiment(req: SentimentRequest) -> SentimentResponse:
    results: list[SentimentItem] = []
    counts = Counter({"positive": 0, "neutral": 0, "negative": 0})

    for text in req.texts:
        label, score = classify_text(text)
        counts[label] += 1
        results.append(SentimentItem(text=text, label=label, score=score))

    total = max(1, len(req.texts))
    sentiment_percentage = {
        "positive": round((counts["positive"] / total) * 100, 2),
        "neutral": round((counts["neutral"] / total) * 100, 2),
        "negative": round((counts["negative"] / total) * 100, 2),
    }

    return SentimentResponse(
        sentiment_percentage=sentiment_percentage,
        classifications=results,
    )
