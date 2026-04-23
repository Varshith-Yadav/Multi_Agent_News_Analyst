# Multi-Agent News Analyst

Generative AI platform to aggregate, verify, analyze, and synthesize news from diverse sources in near real-time.

## Repository Structure

- `ingestion/` - News ingestion microservice (connectors, scheduling, deduplication).
- `backend/` - Core API for agents, reports, trends, and verification.
- `ui/` - Web dashboard.
- `agents/` - Specialized AI agent logic.
- `apps/` - Reserved for other runtime apps (e.g., worker).
- `services/` - Shared domain services (fact-checking, ranking, source registry, etc.).
- `pipelines/` - Streaming and batch processing pipelines.
- `packages/` - Reusable shared modules, schemas, prompts, and evaluation assets.
- `infra/` - Deployment and operations infrastructure.
- `data/` - Local data zones for raw, staged, curated, and vectorized artifacts.
- `tests/` - Unit, integration, end-to-end, and agent evaluation tests.
- `docs/` - Architecture, product, API, and runbooks.
- `scripts/` - Utility scripts for setup, maintenance, and operations.

## Ingestion Service

- Location: `ingestion`
- Run:

```bash
pip install -r requirements.txt
uvicorn news_ingestion.main:app --app-dir ingestion/src --reload --port 8010
```

## Core API (Phase 2–3)

- Location: `backend`
- Run:

```bash
pip install -r requirements.txt
set PYTHONPATH=agents
uvicorn mana_api.main:app --app-dir backend/src --reload --port 8020
```

## Web Dashboard

- Location: `ui`
- Run:

```bash
cd ui
npm install
npm run dev
```

## API Authentication and RBAC

Protected endpoints use OAuth2 password flow with JWT bearer tokens.

1. Sign up (optional, auto-login token returned):

```bash
curl -X POST http://localhost:8000/signup \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"newuser\",\"password\":\"strongpass123\"}"
```

2. Fetch token:

```bash
curl -X POST http://localhost:8000/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=analyst&password=analyst123"
```

3. Use token with protected APIs:

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"AI regulation\",\"report_format\":\"weekly_trend_report\"}"
```

Roles:
- `viewer`: can fetch results and send follow-up questions
- `analyst`: viewer + can submit analysis jobs
- `admin`: full access

## LLM Configuration (Provider-Agnostic)

Default runtime is Gemini (OpenAI-compatible endpoint), but you can switch providers by env only.

Primary model:

```bash
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
LLM_MODEL=gemini-2.0-flash-lite
LLM_API_KEY_ENV=GEMINI_API_KEY
GEMINI_API_KEY=your_real_key_here
```

Optional cross-provider fallbacks:

```bash
LLM_FALLBACKS_JSON=[{"name":"openai-mini","base_url":"https://api.openai.com/v1","model":"gpt-4o-mini","api_key_env":"OPENAI_API_KEY"},{"name":"ollama-local","base_url":"http://host.docker.internal:11434/v1","model":"llama3.2:3b","api_key":"ollama"}]
```

Fallback order is: primary model first, then entries from `LLM_FALLBACKS_JSON` in listed order.
