# SAVJ Security Audit & Remediation Register

**Scope reviewed:** `phase-16/launch-hardening` (repository snapshot), not the deployed service.  
**Review date:** 2026-10-13  
**Status:** Code review plus targeted hardening and regression-test additions; this is not a penetration test or a production security certification.

## Summary

The repository has a React/Vite frontend and a FastAPI/SQLAlchemy backend on the phase-16 branch. The default `main` branch does not yet contain the full-stack backend. Phase 2's merge conflict has been resolved and its CI passed, but the phase branches remain stacked and are not yet consolidated into `main`. Do not merge this branch directly to `main` out of order.

### Findings and disposition

| # | Check | Initial finding | Required action / status |
|---:|---|---|---|
| 1 | SQL injection | Database access reviewed uses SQLAlchemy expressions; no raw SQL injection sink identified in inspected routes. | Continue SAST and test every dynamic query. |
| 2 | XSS | API schemas constrain lengths; the frontend uses React rendering and Nginx now sends a restrictive Content-Security-Policy (including self-only scripts and explicit OpenStreetMap tile images). Browser-level payload tests were not executed. | Keep React escaping, prohibit unsafe HTML sinks, and validate the policy against the built site and stored/reflected XSS test cases. |
| 3 | CSRF | Production authentication now uses Secure, HttpOnly, SameSite=Lax access cookies and validates Origin on cookie-authenticated state-changing requests; development retains bearer tokens. Browser-level CSRF tests remain unrun. | Keep the Origin allowlist aligned with deployment origins and verify cross-site requests against the deployed reverse proxy and browser. |
| 4 | File uploads | Proof uploads are participant-authorized, capped at 8 MiB before decoding, validated with Pillow, limited to single-frame images and 40 MP, re-encoded to strip ancillary metadata, and stored outside frontend static assets with restrictive file permissions. Malware scanning and private object storage are absent. | Image decode/re-encode and pixel/frame limits implemented; add malware scanning, quotas, and private object storage before public launch. |
| 5 | IDOR / BOLA | Task messages and proof endpoints check task participation. Task details and filtered task lists previously exposed accepted/in-progress tasks to any authenticated account. | Fixed in this PR: non-open tasks are listed and retrieved only for the requester/assigned worker; unknown/private detail lookups return 404. Regression tests cover outsider access. Recheck all object routes as features grow. |
| 6 | Rate limiting | In-process login/register rate limiting is implemented (10 login or 5 registration attempts per IP per 60 seconds); it resets on restart and is not shared across workers. | Add shared-store limits at the ingress/API gateway for all instances, plus quotas for uploads/messages and other costly routes before public launch. |
| 7 | JWT secrets | Production config rejects short/default secrets and SQLite. Token decoder verifies HMAC and expiry, but does not fully validate JWT header/claim shape. | Implemented strict HS256 header/signature/claim validation and malformed/tampered-token tests. |
| 8 | Exposed API secrets | No live secrets were intentionally added by this audit. Repository-wide secret scanning is added in CI. | Rotate any exposed credential immediately; keep deployment secrets in a secret manager. |
| 9 | Password hashing | PBKDF2-HMAC-SHA256 uses 310,000 iterations and a random salt. | Keep the work factor current and add password-hash regression tests. |
| 10 | MFA | No MFA workflow/provider was identified. | Product/security feature not implemented; select TOTP or a managed identity provider before launch. |
| 11 | CORS | Production config rejects wildcard origins and lists explicit origins. | Confirm deployed origin list; CORS is not an authorization control. |
| 12 | Token/session storage | Production frontend builds no longer persist bearer tokens in localStorage. Production login sets a Secure, HttpOnly, SameSite=Lax cookie; cookie-authenticated writes require an allowed Origin. Server-side token-version checks revoke previously issued access tokens on logout. Development mode still uses localStorage for convenience; refresh-token rotation and browser XSS/CSRF acceptance tests remain outstanding. | Keep production session cookies same-origin, implement a tested renewal/recovery policy, prohibit unsafe HTML sinks, and validate the deployed CSP and session behavior in real browsers. |
| 13 | Client-side-only permissions | Backend task transitions and proof/message routes contain server-side checks. Frontend-only permission paths were not fully exercised. | Keep every authorization decision server-side and test with forged API requests. |
| 14 | Row-level security | No PostgreSQL RLS policies were identified. App-layer checks are present in selected routes. | Add RLS only with migrations, least-privilege DB roles, and tests; otherwise document and test application authorization. |
| 15 | Webhook signatures | No webhook receiver/payment integration was identified. | Not applicable until a webhook exists; verify signatures against raw request bytes and enforce replay/idempotency controls when added. |
| 16 | SSRF | No user-controlled server-side URL-fetch feature was identified in reviewed routes. | Reassess if URL previews, imports, callbacks, or remote image fetching are introduced. |
| 17 | Source maps / browser policy | Nginx now sends a Content-Security-Policy; source-map publication was not verified against a built artifact or deployed response. | Verify the deployed CSP and ensure production source maps are not publicly published unless access-controlled and intentionally required. |
| 18 | Default credentials | Production rejects weak/default JWT secrets; no seeded default account was identified in reviewed files. | Check deployment, database, and admin credentials outside Git before release. |
| 19 | Sensitive logs | No explicit credential logging was identified in inspected excerpts; runtime/deployment logs were not available. | Redact Authorization headers, passwords, tokens, personal data, and uploaded content; review host logs. |
| 20 | Vulnerable dependencies | Initial audits found vulnerable frontend chains and pytest 8.4.2. Dependencies were upgraded, a committed `package-lock.json` was generated in GitHub Actions, and `npm ci` plus `npm audit --audit-level=high` passed. On the code head preceding the latest UI/doc-only changes, npm/pip audits, CodeQL, Gitleaks, frontend CI, backend tests, PostgreSQL migration/API smoke tests, and container builds passed. | Keep lockfile updates reviewed, require `npm ci` in CI/container builds, and verify all checks on the exact final integration PR head. |

## Release gates

- [x] Resolve the Phase 2 branch conflict and verify its CI.
- [ ] Consolidate the intended phase stack into `main` in dependency order before applying this audit to the default branch.
- [ ] Run backend tests, frontend lint/typecheck/build, dependency audits, CodeQL, and secret scanning on the final merged tree; ensure all are green after dependency upgrades.
- [x] Commit a generated `package-lock.json` and use `npm ci` so frontend dependency resolution and audit results are reproducible.
- [ ] Configure shared/distributed gateway rate limiting for all instances and add tests for limits, uploads, and cross-account authorization.
- [x] Email verification and password reset now use hashed, single-use expiring tokens, SMTP STARTTLS support, anti-enumeration responses, and per-process abuse limits; live SMTP delivery still needs configuration and acceptance testing.
- [ ] Add MFA and refresh-token rotation.
- [ ] Verify proof-upload malware handling, private storage permissions, retention, and deletion.
- [x] Add multi-account regression tests for task visibility, lifecycle transitions, proof permissions, ratings, and notification ownership.
- [x] Run PostgreSQL migration and API smoke tests in CI, alongside SQLite API regression tests.
- [ ] Run browser end-to-end tests and direct API authorization checks against the final integrated deployment.
- [ ] Review production headers, HTTPS, source-map publication, database privileges/RLS decision, logs, backups, and deployment secrets.
- [ ] Integrate a compliant KYC provider/manual review and a payment/payout provider before enabling paid work; define refunds, disputes, fees, and settlement.
- [ ] Perform staging DAST and an independent penetration test before public launch.

**Important:** A checklist item marked absent or not verified is not a fix. Passing CI is evidence about the tested commit, not proof that the live deployment is secure.
