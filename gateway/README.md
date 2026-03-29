# Gateway Service

This module handles authentication and orchestrates requests to stat and nlp services.

## Prerequisites

- Node.js 20+
- Stat service running (default: `http://localhost:8002`)
- NLP service running (default: `http://localhost:8001`)

## Run Without Docker

1. Open a terminal in this folder:

```bash
cd gateway
```

2. Install dependencies:

```bash
npm install
```

3. Configure environment variables (optional if using defaults):

```bash
cp .env.example .env
```

You can edit `.env` if needed:

- `GATEWAY_PORT` (default `8000`)
- `STAT_URL` (default `http://localhost:8002`)
- `NLP_URL` (default `http://localhost:8001`)
- `JWT_SECRET` (default `supersecret`)
- `DEMO_USER` (default `admin`)
- `DEMO_PASS` (default `admin123`)

4. Start the service:

```bash
npm run dev
```

## Health Check

```bash
curl http://localhost:8000/health
```

## Key Endpoints

- `POST /auth/login`
- `POST /api/dashboard` (requires Bearer token)
