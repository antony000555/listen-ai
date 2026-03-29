# Stat Service

This module filters posts and computes:

- mention count
- top keywords
- trend points (posts over time)
- example posts

## Prerequisites

- Go 1.24+ recommended (module uses `toolchain go1.24.3`)

## Run Without Docker

1. Open a terminal in this folder:

```bash
cd stat
```

2. Download dependencies:

```bash
go mod tidy
```

3. (Optional) Configure environment variables:

```bash
export STAT_PORT=8002
export SQLITE_PATH=./listenai.db
```

4. Start the service:

```bash
go run .
```

## Health Check

```bash
curl http://localhost:8002/health
```

## Example Request

```bash
curl -X POST http://localhost:8002/stats \
  -H "Content-Type: application/json" \
  -d '{
    "include_keywords": ["listen ai", "dashboard"],
    "exclude_keywords": ["spam"],
    "from_date": "2026-03-01",
    "to_date": "2026-03-29",
    "example_limit": 5,
    "post_limit": 500
  }'
```
