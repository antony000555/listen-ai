#!/usr/bin/env python3
"""Download posts CSV (optional) and import it into SQLite posts table.

CSV format:
name,date,content

Date format:
YYYY-MM-DD
"""

from __future__ import annotations

import argparse
import csv
import re
import sqlite3
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import posts.csv into SQLite")
    parser.add_argument(
        "--db",
        default="./data/listenai.db",
        help="Path to SQLite DB (default: ./data/listenai.db)",
    )
    parser.add_argument(
        "--csv",
        default="./posts.csv",
        help="Path to CSV file (default: ./posts.csv)",
    )
    parser.add_argument(
        "--platform",
        default="x",
        help="Platform value for inserted rows (default: x)",
    )
    return parser.parse_args()


def ensure_posts_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            author TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )


def download_csv_with_gdown(drive_url: str, output_csv: Path) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["gdown", drive_url, "-O", str(output_csv)]
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError as exc:
        raise RuntimeError("gdown is not installed. Run: pip install gdown") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"gdown download failed with exit code {exc.returncode}") from exc


def import_posts(db_path: Path, csv_path: Path, platform: str) -> dict[str, int]:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    conn = sqlite3.connect(db_path)
    ensure_posts_table(conn)

    inserted = 0
    skipped_existing = 0
    bad_rows = 0

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        expected = {"name", "date", "content"}
        if set(reader.fieldnames or []) != expected:
            raise ValueError(
                f"Unexpected CSV headers: {reader.fieldnames}; expected name,date,content"
            )

        with conn:
            for row in reader:
                author = (row.get("name") or "").strip()
                date_str = (row.get("date") or "").strip()
                content = (row.get("content") or "").strip()

                if not author or not content or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_str):
                    bad_rows += 1
                    continue

                created_at = f"{date_str}T00:00:00Z"

                exists = conn.execute(
                    """
                    SELECT 1
                    FROM posts
                    WHERE author = ? AND content = ? AND created_at = ?
                    LIMIT 1
                    """,
                    (author, content, created_at),
                ).fetchone()

                if exists:
                    skipped_existing += 1
                    continue

                conn.execute(
                    """
                    INSERT INTO posts(platform, author, content, created_at)
                    VALUES(?, ?, ?, ?)
                    """,
                    (platform, author, content, created_at),
                )
                inserted += 1

    total = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    conn.close()

    return {
        "inserted": inserted,
        "skipped_existing": skipped_existing,
        "bad_rows": bad_rows,
        "total_posts": total,
    }


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    db_path = (root / args.db).resolve() if not Path(args.db).is_absolute() else Path(args.db)
    csv_path = (root / args.csv).resolve() if not Path(args.csv).is_absolute() else Path(args.csv)

    try:
        result = import_posts(db_path=db_path, csv_path=csv_path, platform=args.platform)
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(
        {
            "db": str(db_path),
            "csv": str(csv_path),
            **result,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
