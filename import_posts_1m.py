import sqlite3
import pandas as pd
import joblib
import re
import math
import os

print('Loading models...')
vectorizer = joblib.load('c:/Users/Antony/Documents/GitHub/listen-ai/nlp/tfidf_vectorizer.pkl')
model = joblib.load('c:/Users/Antony/Documents/GitHub/listen-ai/nlp/svm_model.pkl')

print('Loading original data...')
df = pd.read_csv('data/posts.csv')
original_count = len(df)
print(f'Original rows: {original_count}')

print('Extracting unique texts and predicting sentiment...')
unique_texts = df['content'].fillna('').unique()
X = vectorizer.transform(unique_texts)
y_pred = model.predict(X)
sentiment_map = dict(zip(unique_texts, y_pred))

def tokenize(text):
    return [w for w in re.findall(r"[a-zA-Z']+|[\u4e00-\u9fff]+", text.lower()) if len(w) > 1]

print('Tokenizing unique texts...')
token_map = {text: tokenize(text) for text in unique_texts}

print('Expanding dataset to 1,000,000 rows...')
duplicator_count = math.ceil(1000000 / original_count)
df_1m = pd.concat([df]*duplicator_count, ignore_index=True).head(1000000)
df_1m['content'] = df_1m['content'].fillna('')

print('Applying precomputed maps and format adjustments...')
# Fix column names to match DB
df_1m['author'] = df_1m['name']
df_1m['created_at'] = df_1m['date'] + 'T00:00:00Z'
df_1m['platform'] = 'x'
df_1m['sentiment'] = df_1m['content'].map(sentiment_map).fillna('neutral')

# Writing to SQLite
print('Connecting to SQLite...')
if os.path.exists('data/listenai.db'):
    os.remove('data/listenai.db')

conn = sqlite3.connect('data/listenai.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT,
    author TEXT,
    content TEXT,
    created_at TEXT,
    sentiment TEXT,
    sentiment_score REAL
)
''')

cursor.execute('''
CREATE TABLE post_tokens (
    post_id INTEGER,
    token TEXT
)
''')

print('Inserting 1M posts...')
df_posts = df_1m[['platform', 'author', 'content', 'created_at', 'sentiment']].copy()
df_posts['sentiment_score'] = 1.0

# pd.to_sql is slow for 1M rows if not batched natively, but should be ok for sqlite
df_posts.to_sql('posts', conn, if_exists='append', index=False)

print('Creating token inserts...')
# Generate bulk inserts for post_tokens
post_tokens = []
for idx, text in enumerate(df_1m['content']):
    post_id = idx + 1
    tokens = token_map.get(text, [])
    for t in tokens:
        post_tokens.append((post_id, t))

print(f'Inserting {len(post_tokens)} tokens...')
# Use executemany in chunks
chunk_size = 500000
for i in range(0, len(post_tokens), chunk_size):
    cursor.executemany("INSERT INTO post_tokens (post_id, token) VALUES (?, ?)", post_tokens[i:i+chunk_size])

print('Creating Indexes (this might take a minute)...')
cursor.execute("CREATE INDEX idx_sentiment ON posts(sentiment)")
cursor.execute("CREATE INDEX idx_created_at ON posts(created_at)")
cursor.execute("CREATE INDEX idx_post_tokens_token ON post_tokens(token)")
cursor.execute("CREATE INDEX idx_post_tokens_id ON post_tokens(post_id)")

conn.commit()
conn.close()
print('Done!')