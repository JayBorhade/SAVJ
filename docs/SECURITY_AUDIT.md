# SAVJ Security Audit & Remediation Register

**Scope reviewed:** `phase-16/launch-hardening` (repository snapshot), not the deployed service.  
**Review date:** 2026-10-12  
**Status:** Initial code review; this is not a penetration test or a production security certification.

## Summary

The repository has a React/Vite frontend and a FastAPI/SQLAlchemy backend on the phase-16 branch. The default `main` branch does not contain that full-stack backend, and the phase branches are stacked; phase 2 is documented as a merge blocker. Do not merge this branch directly to `main` ahead of the stack.

### Findings and disposition

| # | Check | Initial finding | Required action / status |
|---:|---|---|---|
| 1 | SQL injection | Database access reviewed uses SQLAlchemy expressions; no raw SQL injection sink identified in inspected routes. | Continue SAST and test every dynamic query. |
| 2 | XSS | API schemas constrain lengths, but frontend rendering and browser-level payload tests were not executed. | Verify React escaping; prohibit unsafe HTML sinks and test stored payloads. |
| 3 | CSRF | API uses bearer authorization; no cookie session was identified in reviewed API. | If cookie auth is introduced, add CSRF tokens and SameSite/Origin checks. |
| 4 | File uploads | Proof uploads are participant-authorized, capped at 8 MiB before decoding, validated with Pillow, limited to single-frame images and 40 MP, re-encoded to strip ancillary metadata, and stored outside frontend static assets with restrictive file permissions. Malware scanning and private object storage are absent. | Image decode/re-encode and pixel/frame limits implemented; add malware scanning, quotas, and private object storage before public launch. |
| 5 | IDOR / BOLA | Task messages and proof endpoints check task participation; task detail is available to any authenticated user by design. | Add regression tests for every object endpoint and confirm task visibility policy. |
| 6 | Rate limiting | In-process login/register rate limiting is implemented (10 login or 5 registration attempts per IP per 60 seconds); it resets on restart and is not shared across workers. | Add shared-store limits at the ingress/API gateway for all instances, plus quotas for uploads/messages and other costly routes before public launch. |
| 7 | JWT secrets | Production config rejects short/default secrets and SQLite. Token decoder verifies HMAC and expiry, but does not fully validate JWT header/claim shape. | Implemented strict HS256 header/signature/claim validation and malformed/tampered-token tests. |
| 8 | Exposed API secrets | No live secrets were intentionally added by this audit. Repository-wide secret scanning is added in CI. | Rotate any exposed credential immediately; keep deployment secrets in a secret manager. |
| 9 | Password hashing | PBKDF2-HMAC-SHA256 uses 310,000 iterations and a random salt. | Keep the work factor current and add password-hash regression tests. |
| 10 | MFA | No MFA workflow/provider was identified. | Product/security feature not implemented; select TOTP or a managed identity provider before launch. |
| 11 | CORS | Production config rejects wildcard origins and lists explicit origins. | Confirm deployed origin list; CORS is not an authorization control. |
| 12 | Tokens in localStorage | Main-branch UI is a demo and does not implement real authentication. | When auth is integrated, prefer short-lived access tokens in memory and secure HttpOnly cookies/refresh-token rotation where appropriate; do not put long-lived credentials in localStorage. |
| 13 | Client-side-only permissions | Backend task transitions and proof/message routes contain server-side checks. Frontend-only permission paths were not fully exercised. | Keep every authorization decision server-side and test with forged API requests. |
| 14 | Row-level security | No PostgreSQL RLS policies were identified. App-layer checks are present in selected routes. | Add RLS only with migrations, least-privilege DB roles, and tests; otherwise document and test application authorization. |
| 15 | Webhook signatures | No webhook receiver/payment integration was identified. | Not applicable until a webhook exists; verify signatures against raw request bytes and enforce replay/idempotency controls when added. |
| 16 | SSRF | No user-controlled server-side URL-fetch feature was identified in reviewed routes. | Reassess if URL previews, imports, callbacks, or remote image fetching are introduced. |
| 17 | Source maps | Build/deployment configuration was not validated in a built artifact. | Do not publish production source maps publicly unless access-controlled and intentionally required. |
| 18 | Default credentials | Production rejects weak/default JWT secrets; no seeded default account was identified in reviewed files. | Check deployment, database, and admin credentials outside Git before release. |
| 19 | Sensitive logs | No explicit credential logging was identified in inspected excerpts; runtime/deployment logs were not available. | Redact Authorization headers, passwords, tokens, personal data, and uploaded content; review host logs. |
| 20 | Vulnerable dependencies | Dependency ranges exist; installed dependency tree and advisories were not run in this remote review. | CI now includes dependency/security checks; fix high/critical findings and pin reproducible lockfiles. |

## Release gates

- [ ] Resolve the stacked PR dependency / phase-2 conflict and integrate the intended backend before applying the audit to the default branch.
- [ ] Run backend tests, frontend lint/typecheck/build, dependency audits, CodeQL, and secret scanning on the final merged tree.
- [ ] Configure shared/distributed gateway rate limiting for all instances and add tests for limits, uploads, and cross-account authorization.
- [ ] Add MFA/account recovery and email verification only with a defined provider and secure token lifecycle.
- [ ] Verify proof-upload malware handling, private storage permissions, retention, and deletion.
- [ ] Test authorization using multiple accounts and direct API requests.
- [ ] Review production headers, HTTPS, source-map publication, database privileges/RLS decision, logs, backups, and deployment secrets.
- [ ] Perform staging DAST and an independent penetration test before public launch.

**Important:** A checklist item marked absent or not verified is not a fix. Passing CI is evidence about the tested commit, not proof that the live deployment is secure.
