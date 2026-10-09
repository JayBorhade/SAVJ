# Phase 6 — Private task proof uploads

## Delivered
- Add relational metadata for task proof files.
- Accept before/after image uploads only from the assigned worker while a task is in progress.
- Restrict file types by inspecting JPEG, PNG and WebP file signatures (do not trust the supplied MIME type).
- Enforce an 8 MiB per-image limit and reject empty/unsupported uploads.
- Store files under a private server-side directory, outside the frontend static asset tree; use UUID storage names and sanitized display filenames.
- Expose metadata listing and authenticated file retrieval only to task participants.
- Connect the task UI to upload both proof images before submitting a task for approval.
- Ignore private upload directories in Git and add API tests for successful upload, access restrictions and invalid file rejection.

## Important deployment notes
The private local filesystem adapter is suitable only for local/development deployments with a persistent, access-controlled disk. It is not a substitute for managed private object storage in a horizontally scaled production environment. Production should use private S3-compatible storage with short-lived authorized downloads, malware scanning, retention/deletion rules, backup policy and upload rate limits. Existing databases created before this phase need a schema migration; SQLAlchemy create_all does not alter existing tables. Alembic migrations and production storage are subsequent release blockers.
