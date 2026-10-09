# Phase 16 — Launch hardening and release gates

## What this phase does

- Rejects weak/default JWT secrets in production.
- Rejects SQLite in production so deployment cannot silently use an ephemeral local database.
- Rejects wildcard production CORS and invalid token lifetimes.
- Expands CI triggers to all phase branches and pull requests targeting phase branches, with read-only repository permissions.
- Documents the remaining real-world launch gates and operator runbook.

## Required before a public deployment

### 1. Infrastructure and secrets
- Use a managed PostgreSQL service with automated backups, point-in-time recovery, private networking, and tested restoration.
- Generate a unique random JWT_SECRET with at least 32 characters; keep it in the host secret manager, never Git.
- Set APP_ENV=production, DATABASE_URL, and CORS_ORIGINS to the exact trusted HTTPS frontend origin(s). Wildcards are rejected.
- Configure HTTPS, DNS, security alerts, log retention, uptime monitoring, and a documented incident/contact process.
- Configure persistent private object storage for proof images, upload malware scanning, retention/deletion policy, and access audit logs. The current Compose volume is a single-host self-hosting option, not managed production storage.
- Test backup restoration and database migrations against a staging copy before rollout.

### 2. Identity, account recovery, and worker trust
- Email verification and password reset require an email delivery provider, signed single-use tokens, expiry, anti-enumeration responses, and abuse controls.
- KYC requires an approved identity-verification provider or documented manual review, consent, secure document handling, reviewer permissions, status history, and deletion/retention rules. A profile purpose or skills list is not KYC.
- Do not display verified badges until verification has actually succeeded and the server enforces the status.

### 3. Payments
- Select a provider appropriate for India and the marketplace model; complete merchant onboarding, settlement/refund/dispute policy, webhook signature verification, idempotency, and reconciliation.
- Until these exist, do not collect or advertise in-app payments. Task budgets are listing values only and must not be represented as payment processing.

### 4. Release acceptance checklist
- [ ] Register, log in, restore session, update profile, and sign out in a real browser.
- [ ] Requester posts a task; worker discovers and accepts it; requester/worker permissions are verified with separate accounts.
- [ ] Worker starts task and uploads before/after proof; outsider cannot read proof or messages; requester approves or cancels according to allowed states.
- [ ] Create a community drive, join it from a second account, and verify capacity and duplicate-join behavior.
- [ ] Verify map permission denial, geolocation permission, coordinate-less tasks, narrow/mobile layouts, and keyboard navigation.
- [ ] Exercise empty, loading, offline, API error, expired-token, and duplicate-submit states.
- [ ] Verify database migration from a backup copy, restore backup, and verify logs/alerts.
- [ ] Complete security review and dependency/container scanning; fix all high/critical findings.
- [ ] Obtain product/legal review for marketplace terms, privacy notice, consent, worker safety, disputes, refunds, and data retention.

## Local Docker smoke test

1. Copy .env.compose.example to .env and replace every placeholder with generated values.
2. Keep CORS_ORIGINS=http://localhost:8080 for local Compose only; set the actual HTTPS frontend origin for a public deployment.
3. Run docker compose config, then docker compose up --build -d.
4. Check docker compose ps, docker compose logs --tail=200 api web db, and open http://localhost:8080.
5. Verify http://localhost:8000/health locally. Before any public release, test the full checklist above against staging.

## Honest status

CI is automated evidence for the jobs in the workflow, not proof of a browser-accepted or production-ready release. This phase does not create provider accounts, configure production hosting, perform KYC, send email, process payments, or deploy the service. Those actions require owner-controlled accounts, credentials, policy decisions, and a staging/production environment.
