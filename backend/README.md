# SAVJ Backend

FastAPI + SQLAlchemy backend for the SAVJ environmental community platform.

## Run locally (Windows PowerShell)

From the repository root:

    py -3.11 -m venv backend/.venv
    .\backend\.venv\Scripts\Activate.ps1
    python -m pip install -r backend/requirements.txt
    Copy-Item backend/.env.example backend/.env
    python -m uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000

Open http://127.0.0.1:8000/docs for interactive API docs and http://127.0.0.1:8000/health for health.

## Implemented

- Registration/login with PBKDF2 password hashes and expiring signed bearer tokens
- Authenticated profile read/update
- Task create/list/detail and server-enforced accept/start/submit/approve/cancel lifecycle
- Community drive create/list/join with unique participation and capacity checks
- Task-participant-only messaging\n- Private before/after task proof uploads (JPEG/PNG/WebP, 8 MB limit) with metadata, task-participant-only listing/download, and worker/status authorization
- Verified completion and drive participation impact counters
- SQLAlchemy relational models; SQLite locally and PostgreSQL via configured URL
- Environment-driven CORS configuration

## API

- POST /api/v1/auth/register and /api/v1/auth/login
- GET/PATCH /api/v1/me
- GET/POST /api/v1/tasks and GET /api/v1/tasks/{id}
- POST /api/v1/tasks/{id}/accept, /start, /submit, /approve, /cancel
- GET/POST /api/v1/drives and POST /api/v1/drives/{id}/join
- GET /api/v1/me/impact
- GET/POST /api/v1/tasks/{id}/messages

## Production limitations

Not deployed or connected to the frontend yet. External identity/OAuth, email verification, password reset, rate limiting, database migrations, secure proof-file uploads, KYC, payments, geospatial queries, real-time messaging and end-to-end tests remain future work. Do not use this development backend for real paid jobs until proof storage and deployment security are in place. Configure a strong unique JWT_SECRET, managed PostgreSQL, HTTPS, restrictive CORS and monitoring before production. Never commit .env, database files or credentials.
