# Phase 11 — Containerized full stack

## Delivered
- Add a multi-stage frontend container with Nginx SPA fallback and same-origin API reverse proxy.
- Route browser API calls through the frontend origin in production builds.
- Extend Docker Compose to run frontend, FastAPI backend, and PostgreSQL with health checks.
- Keep the API host port bound to loopback for local use, run the backend as non-root, and persist database/private proof uploads in named volumes.
- Add a local environment template and full-stack startup/operations documentation.

## Not equivalent to a public launch
This creates a reproducible self-hosted stack. A public launch still needs HTTPS/TLS, managed secrets, managed database/object storage, off-site backups and restore tests, monitoring/alerting, upload malware scanning and retention controls, and external provider credentials where required. The assistant cannot safely invent or provision those account secrets.
