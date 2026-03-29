# Frontend Service

This module provides the dashboard UI for social listening.

## Prerequisites

- Python 3.11+
- The gateway service running locally (default: `http://localhost:8000`)

## Run Without Docker

1. Open a terminal in this folder:

```bash
cd frontend
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. (Optional) Set gateway URL:

```bash
export GATEWAY_URL=http://localhost:8000
```

5. Start the app:

```bash
streamlit run app.py --server.port 8501
```

## Access

- UI: `http://localhost:8501`

## Notes

- Default demo login is handled by gateway:
  - Username: `admin`
  - Password: `admin123`
