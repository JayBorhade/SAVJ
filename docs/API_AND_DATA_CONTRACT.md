# SAVJ API and Data Contract

**Review scope:** current implementation on `security/hardening-phase16`  
**Deployment status:** repository code only; no live production deployment has been verified.

## Conventions

- API base path: `/api/v1`.
- IDs are integer database IDs in the current API.
- Timestamps are ISO 8601; scheduled task/drive timestamps must include a timezone and be in the future.
- Request validation uses Pydantic. Validation failures use FastAPI's `detail` response format; the custom `error.code` envelope shown in earlier drafts is not implemented.
- Production authentication uses a Secure, HttpOnly, SameSite=Lax access cookie and validates `Origin` on cookie-authenticated state-changing requests. Development/test environments retain bearer-token compatibility.
- Email verification and password recovery use hashed, expiring, single-use tokens. Production requires a configured SMTP STARTTLS provider and an HTTPS `PUBLIC_APP_URL` whose origin is included in `CORS_ORIGINS`.
- API access does not imply KYC verification, payment settlement, or identity proof.

## Implemented endpoints

| Method | Endpoint | Purpose and authorization |
|---|---|---|
| POST | `/api/v1/auth/register` | Create account. Production sends email verification and does not issue a session until verified. |
| POST | `/api/v1/auth/login` | Authenticate; production returns an HttpOnly cookie, development returns a bearer token. |
| POST | `/api/v1/auth/logout` | Increment token version, revoke earlier tokens, and clear the cookie. |
| POST | `/api/v1/auth/verification-request` | Anti-enumeration verification-email request. |
| POST | `/api/v1/auth/verify-email` | Consume a valid single-use verification token. |
| POST | `/api/v1/auth/password-reset/request` | Anti-enumeration password-reset request. |
| POST | `/api/v1/auth/password-reset/confirm` | Consume reset token, update password, and revoke earlier sessions. |
| GET | `/api/v1/me` | Read the authenticated user's profile. |
| PATCH | `/api/v1/me` | Update profile, purpose, skills, and tools. |
| GET | `/api/v1/tasks` | Discover open tasks plus non-open tasks visible to the requester/assigned worker; supports filters and pagination. |
| POST | `/api/v1/tasks` | Create a task with budget, schedule, location, required skills, and required tools. |
| GET | `/api/v1/tasks/{task_id}` | Read open task details or participant-only non-open task details. |
| POST | `/api/v1/tasks/{task_id}/accept` | Accept an eligible open task; checks worker purpose and mandatory skills/tools. |
| POST | `/api/v1/tasks/{task_id}/start` | Assigned worker starts work; requester may return awaiting-approval work for rework. |
| POST | `/api/v1/tasks/{task_id}/submit` | Assigned worker submits only after fresh before-and-after proof has been uploaded. |
| POST | `/api/v1/tasks/{task_id}/approve` | Requester approves submitted work and records verified completion impact. |
| POST | `/api/v1/tasks/{task_id}/cancel` | Participant-authorized cancellation where allowed by the state machine. |
| POST | `/api/v1/tasks/{task_id}/proofs/{proof_kind}` | Upload a private `before` or `after` image. |
| GET | `/api/v1/tasks/{task_id}/proofs` | List proof metadata for task participants. |
| GET | `/api/v1/proofs/{proof_id}/content` | Retrieve proof image content for authorized participants. |
| GET/POST | `/api/v1/tasks/{task_id}/messages` | Read/send messages scoped to task participants. |
| GET | `/api/v1/drives` | Discover open community drives. |
| POST | `/api/v1/drives` | Create a community drive. |
| POST | `/api/v1/drives/{drive_id}/join` | Join idempotently with a capacity check. |
| GET | `/api/v1/workers` | Search worker profiles, skills/tools, and aggregate task ratings. |
| GET | `/api/v1/tasks/{task_id}/rating` | Read a rating for task participants; returns null if unrated. |
| POST | `/api/v1/tasks/{task_id}/rating` | Requester rates a completed task once, score 1–5. |
| GET | `/api/v1/me/notifications` | List only the authenticated user’s notifications. |
| POST | `/api/v1/me/notifications/{notification_id}/read` | Mark one owned notification read. |
| POST | `/api/v1/me/notifications/read-all` | Mark all of the authenticated user’s notifications read. |
| GET | `/api/v1/me/impact` | Return server-recorded verified completions and joined drives. |

## Core data model

- **User:** email, password hash, display name, locality, purpose, skills, tools, active status, email verification state, token version, creation time.
- **Task:** requester/worker IDs, title, description, category, required skills/tools, public locality, optional private address, optional coordinates, integer minor-unit budget, currency, timezone-aware schedule, state, optimistic version, timestamps.
- **TaskProof:** task/uploader IDs, proof kind, private storage key, original filename metadata, content type, byte size, creation time.
- **TaskRating:** one rating per task, requester and worker IDs, score, private comment, timestamp. Worker directory exposes average and count, not public comments.
- **CommunityDrive / DriveParticipation:** drive metadata, capacity, status and unique user participation.
- **Message:** task ID, sender ID, body and timestamps.
- **ImpactEvent:** server-created completion events. The impact dashboard's medals are derived from verified completions and drive participation.
- **UserNotification:** per-user task/drive activity notices with read state; task state changes, messages, and drive joins create notifications within the same transaction.

## Security and correctness invariants

1. Open tasks are discoverable to authenticated users, but non-requesters receive only the public locality and coordinates rounded to two decimal places; the private address is withheld until acceptance. The requester and assigned worker can see the precise address. Non-open task details and list entries are limited to those participants.
2. State transitions are checked server-side and serialized with PostgreSQL row locks. SQLite does not provide equivalent row-lock behavior; production concurrency tests must run against PostgreSQL.
3. A task cannot be submitted for approval without fresh before-and-after images uploaded by its assigned worker during the current work attempt.
4. Completion impact is recorded only when the requester approves the task. A partial unique index prevents duplicate task-completion events.
5. Task acceptance enforces the task's mandatory skills and tools against the worker profile.
6. Proof images are decoded and re-encoded, format/frame/pixel/output-size limited, and stored outside frontend static assets with restrictive filesystem permissions.
7. Email action tokens are random, stored as SHA-256 hashes, expire, and are single-use. Password reset revokes earlier access tokens.
8. Money is stored as integer minor units. **A budget is not a payment:** payment collection, escrow, worker payouts, refunds and disputes are not implemented.
9. Login/register/email action throttling is process-local defense-in-depth. A shared gateway/distributed limiter is required for multi-worker production.
10. KYC/identity verification, MFA, refresh-token rotation, malware scanning, managed object storage and public moderation/reporting are not implemented. Do not present profiles as KYC-verified.
11. Notifications are user-scoped and do not expose message bodies; task notifications link only to tasks the user can access. Notification delivery is in-app only; email/push delivery is not implemented.
12. The current API returns FastAPI validation/error responses and does not yet attach a universal request ID or custom error code envelope.

## Deployment and release gates

- Run migrations and all tests against the exact release commit and a production-like PostgreSQL service.
- Configure unique secrets, HTTPS origins, SMTP STARTTLS, the public app URL, private upload storage and backups.
- Configure distributed rate limiting, monitoring, alerting, log redaction, backup/restore drills, and object retention/deletion.
- Integrate a compliant KYC provider or reviewed manual process, and a payment/payout provider with verified webhook signatures and idempotency, before enabling paid work.
- Run browser end-to-end journeys, staging DAST, accessibility checks and independent penetration testing.
- No live hosting, real SMTP delivery, payment provider, KYC provider, or independent security certification is claimed by this repository update.
