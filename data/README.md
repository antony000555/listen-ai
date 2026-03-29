# Data

This module contains the SQLite database and helper script for importing post data.

## Files

- `listenai.db`: SQLite database file.
- `import_posts.py`: Download CSV (optional) and import rows into `posts` table.

## CSV Format

The CSV file must have exactly 3 columns:

```csv
name,date,content
```

Date format must be:

```text
YYYY-MM-DD
```
# Setup

1. Download the `posts.csv` file from [Google Drive](https://drive.google.com/file/d/1GCzFt9xFxAlr_FCCJprBqClJE4Qbpu4q/view?usp=sharing)
2. Import the posts into the database with:
```bash
python import_posts.py --csv ./data/posts.csv --db ./data/listenai.db
```

## Behavior

- Creates `posts` table if missing.
- Maps:
  - `name` -> `author`
  - `date` -> `created_at` (stored as `YYYY-MM-DDT00:00:00Z`)
  - `content` -> `content`
- Skips duplicate rows (same `author`, `content`, and `created_at`).
- Prints summary with inserted/skipped/bad row counts.
