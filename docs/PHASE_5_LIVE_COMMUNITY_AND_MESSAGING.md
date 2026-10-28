# Phase 5 — Live community and messaging

## Delivered
- Replaced the static Community page with a backend-backed drive list.
- Added drive creation with required title/location/future start time and optional participant capacity.
- Added join-drive actions, duplicate-join feedback, and refreshed server participant counts.
- Replaced the Messages placeholder with a task-scoped conversation interface.
- Conversations are listed only for tasks where the signed-in user is requester or assigned worker.
- Message retrieval and sending use the API's existing participant-authorized endpoints.
- Extended the typed frontend API client with drive creation, task messages, and impact endpoint methods.

## Verification and limitations
- This phase depends on the Phase 3 API and Phase 4 frontend/API integration branches.
- CI must pass before the phase is considered verified.
- The existing API currently returns tasks to any authenticated user; this frontend filters conversations to the current user's participant tasks, while the message endpoints enforce authorization server-side.
- Messaging is request/refresh based, not real-time. Polling/websockets, notifications, unread counts, and message moderation are not included.
- Community drives are only live when the backend is configured and the user is signed in; no static sample drives are presented as live records.
- Secure proof uploads, map/geocoding/radius search, KYC, migrations, production deployment, and production security hardening remain subsequent phases.
