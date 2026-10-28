# SAVJ Phase 3 — Backend and Database

## Implemented in this branch

- FastAPI application, health endpoint and OpenAPI documentation.
- SQLAlchemy tables for users, tasks, community drives, drive participation, messages and impact events.
- SQLite local-development default; database URL configurable for PostgreSQL.
- Registration/login, PBKDF2 password hashing, signed expiring bearer tokens and profile read/update.
- Server-side task lifecycle permissions and budgets stored as integer paise.
- Community drive create/list/join, unique participation and capacity checks.
- Task-participant-only messaging and impact counters based on verified completion events.
- Automated API tests for auth, duplicate registration, task permissions/lifecycle, drives, messages and impact.

## Local verification (PowerShell)

    py -3.11 -m venv backend/.venv
    .\backend\.venv\Scripts\Activate.ps1
    python -m pip install -r backend/requirements.txt
    python -m pytest backend/tests -q
    python -m uvicorn app.main:app --app-dir backend --reload

## Not production complete

The backend is not deployed or wired to the frontend. Production work still includes managed database migrations, private object storage and proof uploads, KYC, email verification/password reset, rate limiting, deployment secrets/HTTPS, monitoring, geospatial map integration and end-to-end tests. Do not use it for real paid work until proof storage and production security controls exist.
