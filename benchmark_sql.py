import sqlite3
import time
import re

print('Benchmarking on 1,000,000 posts database...')
conn = sqlite3.connect('data/listenai.db')
cursor = conn.cursor()

keyword = '台大' # random search string

# Method 1 (Old Way): Read all records to memory and apply regex + NLP mocking
start = time.time()
cursor.execute('SELECT id, content FROM posts')
all_posts = cursor.fetchall()

matching_posts = []
for p_id, content in all_posts:
    if keyword in content: 
         matching_posts.append((p_id, content))
         
words_count = {}
for p_id, content in matching_posts:
    words = [w for w in re.findall(r"[a-zA-Z']+|[\u4e00-\u9fff]+", content.lower()) if len(w) > 1]
    for w in words:
        words_count[w] = words_count.get(w, 0) + 1
        
old_way_time = time.time() - start
print(f'Old Method (Read to memory + Regex): {old_way_time:.2f} seconds')


# Method 2 (New Way): Native SQL group by with indexes
start = time.time()
cursor.execute('''
    SELECT pt.token, COUNT(pt.token) as cnt
    FROM post_tokens pt
    JOIN posts p ON pt.post_id = p.id
    WHERE pt.token = ?
    GROUP BY pt.token
''', (keyword,))
results = cursor.fetchall()
new_way_time = time.time() - start
print(f'New Method (Pregenerated tokens + SQL JOIN/Indexed): {new_way_time:.2f} seconds')

print(f'\nSpeedup Factor: {old_way_time / new_way_time:.1f}x')
conn.close()