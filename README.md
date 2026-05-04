# Multi-Agent News Analyst

Containerized news analysis platform with a FastAPI backend, Redis-backed worker queue, Postgres storage, and a Vite/React dashboard.

## Production Stack

- `backend` - FastAPI API on port `8000`
- `worker` - asynchronous job processor
- `frontend` - static production build served by Nginx on port `80`
- `postgres` - relational storage
- `redis` - queue and job state store

The production frontend proxies `/api/*` requests to the backend, so the browser talks to a single origin.

## Production Readiness Changes

- Removed deploy-time reliance on dev servers and hot reload
- Added production Docker image for the frontend
- Enforced non-default `AUTH_SECRET_KEY` and `ENCRYPTION_KEY` in `prod`
- Replaced built-in demo users in production with explicit `AUTH_SEED_USERS_JSON`
- Disabled public signup by default in production
- Fixed frontend lint errors that would fail CI

## Deploy

1. Copy the example environment file:

```bash
cp .env.example .env
```

2. Edit `.env` and set these values before deploying:

- `AUTH_SECRET_KEY`
- `ENCRYPTION_KEY`
- `AUTH_SEED_USERS_JSON`
- `XAI_API_KEY` (Grok) or your provider-specific API key
- `FRONTEND_ORIGIN` and `FRONTEND_ORIGINS_CSV`
- `POSTGRES_PASSWORD`

LLM defaults are set to Grok (`LLM_BASE_URL=https://api.x.ai/v1`, `LLM_MODEL=grok-4`).
If Grok is temporarily unavailable, configure `LLM_FALLBACK_MODELS_CSV` / `LLM_FALLBACKS_JSON`.

3. Build and start the stack:

```bash
docker compose up --build -d
```

4. Open the app:

- `http://localhost` if deploying on the same machine
- or your mapped domain if deployed remotely

## Useful Commands

Check merged Compose config:

```bash
docker compose config
```

View logs:

```bash
docker compose logs -f
```

Stop the stack:

```bash
docker compose down
```

## Local Quality Checks

Frontend:

```bash
cd ui
npm run lint
npm run test
npm run build
```

Backend syntax:

```bash
python -m compileall app
```

## Notes

- Production signup is disabled unless `ALLOW_PUBLIC_SIGNUP=true`.
- Seeded users come from `AUTH_SEED_USERS_JSON`; no insecure default users are loaded in `prod`.
- The backend and worker both require Redis and Postgres to be healthy before startup.
