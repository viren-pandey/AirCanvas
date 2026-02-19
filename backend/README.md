# AirCanvas Pro Backend

FastAPI backend for authenticated frame capture, Postgres metadata, S3 object storage, and admin analytics.

## Features

- JWT auth (`/api/v1/auth/register`, `/api/v1/auth/login`, `/api/v1/auth/me`)
- Session tracking (`/api/v1/sessions`, `/api/v1/sessions/{id}/end`)
- Frame upload flow with signed object-storage URLs (`/api/v1/frames/upload-url`, `/api/v1/frames/{id}/complete`)
- User/admin frame listing and gallery filtering
- Admin analytics endpoints and dashboard (`/api/v1/admin/*`, `/admin`)
- Community feed + post creation (`/api/v1/community/posts`)
- User activity timeline (`/api/v1/community/activity`)
- User dashboard UI (`/dashboard`) for login/register + personal gallery + desktop token connection
- Upload rate limiting with `slowapi`

## Quick Start

1. Install dependencies:

```bash
pip install -r backend/requirements.txt
```

2. Configure environment variables in `.env`:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/aircanvas_pro
JWT_SECRET=replace-with-a-strong-secret
JWT_EXP_MINUTES=1440
ADMIN_BOOTSTRAP_SECRET=admin-bootstrap-key

STORAGE_BUCKET=aircanvas-pro
S3_REGION=us-east-1
S3_ENDPOINT_URL=
S3_ACCESS_KEY_ID=
S3_SECRET_ACCESS_KEY=
SIGNED_URL_TTL_SECONDS=900

CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
CORS_ALLOW_CREDENTIALS=false
```

3. Run migrations:

```bash
python -m backend.scripts.run_migrations
```

4. Start API:

```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

5. Open dashboards:

- User dashboard: `http://localhost:8000/dashboard`
- Admin dashboard: `http://localhost:8000/admin`

## Upload Flow

1. Desktop client requests signed URLs with metadata (`brush_mode`, `shape_mode`, `session_id`).
2. Client uploads PNG + thumbnail directly to object storage.
3. Client calls `/complete` to verify metadata and receive signed read URLs.

## Health Endpoints

- `/health`
- `/healthz`

## Docker Hosting

Build image from repository root:

```bash
docker build -f backend/Dockerfile -t aircanvas-backend .
```

Run image:

```bash
docker run --env-file .env -p 8080:8080 aircanvas-backend
```

Startup command runs migrations and serves:

- API: `/api/v1/*`
- User dashboard: `/dashboard`
- Admin dashboard: `/admin`
