# Phase 13 — Task lifecycle polish

## Delivered
- Include requester and assigned-worker identity in the frontend task view model.
- Expose cancellation for non-terminal tasks only to the requester or assigned worker when connected to the backend.
- Ask for confirmation before cancellation and use the server's transition endpoint for authoritative state changes.
- Preserve a clearly labeled local-demo cancellation path when offline.
