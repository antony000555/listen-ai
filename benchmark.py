import sqlite3
import time

conn = sqlite3.connect('./data/listenai.db')
cursor = conn.cursor()

# 1. 測試傳統需要讀出來的方法 (舊架構)
start = time.time()
cursor.execute("SELECT content FROM posts")
count = 0
for row in cursor.fetchall():
    count += 1
print(f"Old Method (Fetch 1M to memory): {time.time() - start:.4f} seconds")

# 2. 測試新架構 (利用 Index 讓 SQLite 完成處理)
start = time.time()
cursor.execute("SELECT sentiment, COUNT(*) FROM posts GROUP BY sentiment")
print("New Method (SQL Group By Index) Result:", cursor.fetchall())
print(f"New Method (SQL Aggregation time): {time.time() - start:.4f} seconds")

start = time.time()
cursor.execute("SELECT pt.token, COUNT(pt.token) as cnt FROM post_tokens pt INNER JOIN posts p ON pt.post_id = p.id WHERE pt.token != '' GROUP BY pt.token ORDER BY cnt DESC LIMIT 5")
print("New Method Top 5 Tokens:", cursor.fetchall())
print(f"New Method Tokens Aggregation time: {time.time() - start:.4f} seconds")