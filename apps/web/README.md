# Web App

Frontend dashboard for the News Ingestion Engine and intelligence workflow.

## Features

- Health and connector visibility
- Manual ingestion trigger (NewsAPI/RSS)
- Ingestion run metrics and status history
- Source registry view
- Recent article cards with source attribution
- Auto-refresh every 30 seconds

## Setup

1. Install dependencies:

```bash
npm install
```

2. Configure API endpoint:

```bash
cp .env.example .env
```

3. Run development server:

```bash
npm run dev
```

## Environment Variables

- `VITE_INGESTION_API_BASE_URL` (default: `http://localhost:8010`)
