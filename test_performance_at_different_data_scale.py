# -*- coding: utf-8 -*-
import sqlite3
import time
import re
import joblib
import os
import pandas as pd
import traceback

print("Loading Real ML Models (TF-IDF & SVM)...")
vectorizer = joblib.load('nlp/tfidf_vectorizer.pkl')
classifier = joblib.load('nlp/svm_model.pkl')

def setup_database(db_name, size, sample_texts):
    if os.path.exists(db_name):
        os.remove(db_name)
    
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("PRAGMA synchronous = OFF")
    cursor.execute("PRAGMA journal_mode = MEMORY")
    
    cursor.execute("CREATE TABLE posts (id INTEGER PRIMARY KEY, content TEXT, sentiment TEXT)")
    cursor.execute("CREATE TABLE post_tokens (post_id INTEGER, token TEXT)")
    
    print(f"\n[{size:,}] Generating {size:,} records in {db_name} (this might take a moment)...")
    
    parsed_samples = []
    for t in sample_texts:
        tokens = re.findall(r"[a-zA-Z']+|[\u4e00-\u9fff]+", str(t).lower())
        parsed_samples.append((str(t), "positive", tokens))
        
    batch_size = 100000
    total_inserted = 0
    
    while total_inserted < size:
        limit = min(batch_size, size - total_inserted)
        posts_data = []
        tokens_data = []
        
        for i in range(limit):
            idx = total_inserted + i + 1
            t_obj = parsed_samples[idx % len(parsed_samples)]
            posts_data.append((idx, t_obj[0], t_obj[1]))
            for tk in t_obj[2]:
                tokens_data.append((idx, tk))
                
        cursor.executemany("INSERT INTO posts (id, content, sentiment) VALUES (?, ?, ?)", posts_data)
        cursor.executemany("INSERT INTO post_tokens (post_id, token) VALUES (?, ?)", tokens_data)
        conn.commit()
        total_inserted += limit
        print(f"  -> Inserted {total_inserted:,}/{size:,}")
        
    print(f"[{size:,}] Creating Indexes...")
    cursor.execute("CREATE INDEX idx_sentiment ON posts(sentiment)")
    cursor.execute("CREATE INDEX idx_token ON post_tokens(token)")
    conn.commit()
    return conn

def test_old_method(conn, size):
    print(f"\n--- Testing Old Method (Read-Time + Full NLP Pipeline) for {size:,} records ---")
    start_time = time.time()
    try:
        cursor = conn.cursor()
        
        print("    1. DB: Fetching ALL POSTS into Python RAM...")
        cursor.execute("SELECT content FROM posts")
        rows = cursor.fetchall()
        contents = [row[0] for row in rows]
        
        print("    2. RAM: Running Regex tokenization on ALL text...")
        word_freq = {}
        for text in contents:
            tokens = re.findall(r"[a-zA-Z']+|[\u4e00-\u9fff]+", text.lower())
            for t in tokens:
                word_freq[t] = word_freq.get(t, 0) + 1
                
        print("    3. ML: Vectorizing text via TF-IDF...")
        X_vec = vectorizer.transform(contents)
        
        print("    4. ML: Running SVM predict()...")
        preds = classifier.predict(X_vec)
        
        sentiment_counts = {}
        for p in preds:
            sentiment_counts[p] = sentiment_counts.get(p, 0) + 1
            
        elapsed = time.time() - start_time
        print(f"    [Old Method Done] Time: {elapsed:.4f} seconds.")
        return elapsed
    except MemoryError:
        print("\n💥 [CRASH] Old Method resulted in MemoryError (OOM)!")
        elapsed = time.time() - start_time
        return "OOM"
    except Exception as e:
        print(f"\n💥 [ERROR] {e}")
        return "Failed"

def test_new_method(conn, size):
    print(f"\n--- Testing New Method (Write-Time + SQL Index) for {size:,} records ---")
    start_time = time.time()
    try:
        cursor = conn.cursor()
        
        print("    1. SQL: Fetching exact Top 10 tokens via GROUP BY...")
        cursor.execute("SELECT token, COUNT(*) FROM post_tokens GROUP BY token ORDER BY COUNT(*) DESC LIMIT 10")
        cursor.fetchall()
        
        print("    2. SQL: Fetching Sentiment distributions via GROUP BY...")
        cursor.execute("SELECT sentiment, COUNT(*) FROM posts GROUP BY sentiment")
        cursor.fetchall()
        
        elapsed = time.time() - start_time
        print(f"    [New Method Done] Time: {elapsed:.4f} seconds.")
        return elapsed
    except Exception as e:
        print(f"\n💥 [ERROR] {e}")
        return "Failed"

df = pd.read_csv('nlp/sentiment_result.csv')
sample_texts = df['content'].dropna().tolist()[:100]

sizes = [5000, 1000000]
results = {}

for size in sizes:
    db_name = f"test_db_{size}.sqlite"
    conn = setup_database(db_name, size, sample_texts)
    
    old_time = test_old_method(conn, size)
    new_time = test_new_method(conn, size)
    
    results[size] = {'old': old_time, 'new': new_time}
    conn.close()

print("\n\n" + "="*70)
print("             PERFORMANCE REPORT")
print("="*70)
for size, res in results.items():
    o_val = f"{res['old']:.4f} sec" if isinstance(res['old'], float) else res['old']
    n_val = f"{res['new']:.4f} sec" if isinstance(res['new'], float) else res['new']
    print(f"Data Scale: {size:,} posts")
    print(f"  [Old Architecture] Dynamic Full Fetch + Regex + TF-IDF/SVM : {o_val}")
    print(f"  [New Architecture] DB Precomputation + B-Tree Tree Index   : {n_val}")
    
    if isinstance(res['old'], float) and isinstance(res['new'], float):
        print(f"  >> Speed Improvement: {res['old']/res['new']:.1f}x Faster")
    print("-" * 70)
