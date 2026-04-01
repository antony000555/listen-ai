import sqlite3
import time

conn = sqlite3.connect('./data/listenai.db')

print('Running old method test (Full Table Scan -> Python RAM processing loop)...')
t1 = time.time()
cur = conn.cursor()
cur.execute('SELECT content FROM posts')
rows = cur.fetchall()
# Simulate passing 1 million rows of text data to string joining/regex
words_count = 0
for row in rows:
    words_count += len(row[0].split())
t1_end = time.time()
print(f'Old Method Extracted {len(rows)} texts, total words: {words_count}, Time: {t1_end - t1:.5f} sec')

print('\nRunning new method test (SQL GROUP BY via Index)...')
t2 = time.time()
cur.execute('SELECT sentiment, COUNT(*) FROM posts GROUP BY sentiment')
res2 = cur.fetchall()
t2_end = time.time()
print(f'New Method Sentiment Aggregation: {res2}, Time: {t2_end - t2:.5f} sec')
