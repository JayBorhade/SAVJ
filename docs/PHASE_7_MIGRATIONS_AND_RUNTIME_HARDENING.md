# Phase 7 — Database migrations and runtime hardening

## Delivered
- Add Alembic configuration and an idempotent initial schema bootstrap for empty databases and pre-existing create_all development databases.
- Remove schema creation from API import/startup so schema lifecycle is explicit.
- Add CI migration smoke test before API tests.
- Add a non-root backend container and Docker Compose stack with PostgreSQL health checks and persistent private proof storage.
- Document environment configuration and local migration commands.

## Migration caveat
The baseline revision creates missing tables but does not alter existing tables. Databases created before the task_proofs model need a follow-up explicit migration that creates task_proofs; the migration smoke test covers a fresh database. Back up existing data before upgrading and use a dedicated revision for existing installations.

## Still required before production
Managed object storage, HTTPS/reverse proxy, secret management, backups/restore drills, rate limiting, monitoring, email verification/password reset, KYC, geospatial queries, end-to-end tests and an actual hosted deployment.