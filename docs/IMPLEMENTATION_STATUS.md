# SAVJ Implementation Status

**Last reviewed:** 2026-10-13  
**Reviewed branch:** `security/hardening-phase16`  
**Integration base:** `phase-16/launch-hardening`  
**Overall status:** Integrated full-stack implementation exists on stacked phase branches; not yet consolidated, deployed, or production-ready.

## Current implementation

### Frontend
- React + TypeScript + Vite desktop-first SAVJ dashboard with responsive layout.
- Personalized onboarding, name greeting, locality chip, task feed, search/category/radius controls, task creation, worker directory, community-drive UI, task messaging, impact/profile screens, map UI, and proof-review components.
- Typed API client connects authentication, profile, task, worker, drive, messaging, impact, and proof routes to FastAPI.
- Browser-local demo data remains available when signed out. Some dashboard sample content is illustrative and must not be mistaken for live backend data.
- Production builds use Secure, HttpOnly, SameSite=Lax access cookies with Origin checks for cookie-authenticated writes; JavaScript does not receive the bearer token. Development retains the local bearer-token flow. Token-version checks revoke previous access tokens on logout; refresh-token rotation is not implemented.

### Backend
- FastAPI + SQLAlchemy API for registration/login, profile, task discovery/lifecycle, worker directory, community drives, task messages, impact totals, and private before/after proof images.
- Passwords use salted PBKDF2-HMAC-SHA256; JWT parsing/signature/claim checks are strict.
- Production configuration rejects weak placeholder JWT secrets, SQLite, wildcard CORS, and invalid production origins.
- Proof uploads are size-limited, decoded/re-encoded, constrained by format/frame/pixel limits, and stored outside the frontend's public assets.
- Task detail and task-list visibility now restrict non-open tasks to the requester and assigned worker. Task acceptance and drive capacity checks use PostgreSQL row locks to reduce concurrent double assignment/overbooking.
- The login/register limiter is process-local defense-in-depth only; it is not a distributed production rate limiter.

### Database and deployment
- SQLAlchemy models, Alembic baseline and task-coordinate migration, Dockerfiles, and Docker Compose with PostgreSQL and a persistent private-upload volume are present on the phase stack.
- Migration downgrade safety needs care: the baseline downgrade drops mapped tables. Never downgrade a database containing user data without a verified backup and reviewed migration plan.
- No live production hosting, managed storage, monitoring, backup/restore drill, or production provider configuration is verified by this repository review.

## Verification state

- Earlier Phase 16 CI passed frontend tests/typecheck/lint/build, backend migration/API tests, and container image builds.
- Earlier security runs passed npm audit, pip-audit, CodeQL, and Gitleaks.
- The latest security PR adds cross-account task-visibility, requester-rework, duplicate acceptance, and drive-capacity regression coverage. CI and security workflows must pass on the latest commit before merge.
- No local shell/browser runtime, live deployment, staging DAST, or independent penetration test was available in this remote-only pass. Those are explicitly **not verified**.
- A committed `package-lock.json` is still missing, so npm dependency resolution is not reproducible yet.

## Integration status and critical blocker

SAVJ's branches are stacked:

`main → phase-1 → phase-2 → phase-3 → phase-4 → phase-5 → phase-6 → phase-7 → phase-8 → phase-9 → phase-10 → phase-11 → phase-12 → phase-13 → phase-14 → phase-15 → phase-16`

Security PR #18 targets `phase-16/launch-hardening`, not `main`. Phase 17 verification is documentation-only and also targets Phase 16. PR #2 (Phase 2) has been reported as dirty/not mergeable; the exact conflict paths require inspection in a local Git checkout. Do not merge later phases out of order or rewrite shared phase branches blindly.

## Release blockers

- [ ] Resolve and verify the Phase 2 merge conflict; consolidate the stacked PRs in dependency order.
- [ ] Generate and commit `package-lock.json`; use `npm ci` for repeatable CI installs and audits.
- [ ] Re-run all CI/security workflows on the final integrated tree.
- [x] Use HttpOnly production access cookies, SameSite protection, Origin validation for cookie-authenticated writes, and server-side token-version revocation on logout.
- [ ] Add refresh-token rotation and a recovery/session-management policy; run browser-based CSRF/XSS acceptance tests.
- [ ] Add shared/distributed rate limits and quotas at the gateway for all instances.
- [x] Implement email verification and password recovery with hashed, single-use expiring tokens, anti-enumeration request endpoints, and SMTP delivery hooks; real SMTP configuration and acceptance testing remain required.
- [ ] Add MFA/managed identity-provider integration and refresh-token rotation.
- [ ] Decide whether PostgreSQL RLS is required; otherwise keep and test application-layer authorization with least-privilege DB roles.
- [ ] Add malware scanning, private object storage, quotas, retention and deletion policies for uploaded proof.
- [ ] Validate deployment secrets, HTTPS, source-map publication, backups/restore, monitoring, and log redaction.
- [ ] Run browser end-to-end journeys and staging DAST; obtain an independent penetration test before public launch.

## Definition of done

SAVJ is ready for a controlled release only after the branch stack is integrated, latest CI and security checks are green, the live deployment is configured and tested, critical release blockers are closed or formally accepted, and real user journeys are verified in a browser. Passing CI alone does not establish production readiness.
