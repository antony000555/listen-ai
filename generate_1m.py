import sqlite3
import random
import time

conn = sqlite3.connect('./data/listenai.db')
cursor = conn.cursor()

# Get available posts to duplicate
cursor.execute("SELECT platform, author, content, created_at, sentiment, sentiment_score FROM posts")
original_posts = cursor.fetchall()
if not original_posts:
    print("Database is empty. Please run import_posts_v2.py first.")
    exit()

print(f"Loaded {len(original_posts)} original posts.")

# Get tokens for original posts to duplicate easily
post_tokens_map = {}
cursor.execute("SELECT id FROM posts")
for row in cursor.fetchall():
    pid = row[0]
    cursor.execute("SELECT token FROM post_tokens WHERE post_id=?", (pid,))
    post_tokens_map[pid] = [r[0] for r in cursor.fetchall()]

# Generate up to 1,000,000
target = 1000000
current_count = len(original_posts)
to_add = target - current_count

print(f"Need to insert {to_add} rows. Starting massive insert...")

start_time = time.time()
batch_size = 10000

for i in range(0, to_add, batch_size):
    posts_batch = []
    tokens_batch = []
    
    # Pre-generate batch for speed
    for _ in range(min(batch_size, to_add - i)):
        original_idx = random.randint(1, len(original_posts))
        post = original_posts[original_idx - 1]
        tokens = post_tokens_map.get(original_idx, [])
        posts_batch.append(post + (tokens,))
    
    with conn:
        for p in posts_batch:
            # Insert post
            cursor.execute("INSERT INTO posts(platform, author, content, created_at, sentiment, sentiment_score) VALUES(?, ?, ?, ?, ?, ?)", p[:6])
            new_id = cursor.lastrowid
            
            # Insert tokens
            if p[6]:
                cursor.executemany("INSERT INTO post_tokens(post_id, token) VALUES(?, ?)", [(new_id, t) for t in p[6]])
    
    print(f"Inserted {i + len(posts_batch)} / {to_add}...")

print(f"Finished in {time.time() - start_time:.2f} seconds.")