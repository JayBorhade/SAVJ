# SAVJ Phase 4 — Frontend/API Integration

## Implemented
- Typed frontend API client with configurable `VITE_SAVJ_API_URL`.
- Account registration and login inside Settings, with bearer token persistence.
- Session restoration on reload, current profile retrieval and server task loading.
- Task creation uses the authenticated backend when signed in.
- Accept/start/approve lifecycle actions call server endpoints when connected.
- Clear fallback to local demo behavior when no backend session is active.
- The UI explicitly warns that proof file selection is not a secure upload and is not sent to the backend.
- CI runs for the Phase 4 branch and pull requests targeting phase branches.

## Run locally (Windows)
1. Start the backend following [backend/README.md](../backend/README.md).
2. In the repository root, copy `.env.example` to `.env.local`.
3. Install frontend dependencies with `npm install`.
4. Run `npm run dev` and open the Vite URL.
5. Open Settings, create an account, then sign in. Server-backed tasks load after authentication.

Default API address: `http://127.0.0.1:8000`. Override it with `VITE_SAVJ_API_URL` in `.env.local`.

## Known limitations
- The backend is a local development service; this branch does not deploy either tier.
- Community drive UI remains a visual/demo list; live drive integration is not complete.
- Proof uploads remain disabled for real API tasks because private object storage and proof metadata endpoints are not implemented.
- Browser token storage is convenient for this prototype but should be reviewed before production; use HTTPS, restrictive CORS, deployment secrets, rate limiting, migrations, and a production session strategy.
- API task data is loaded after sign-in; the existing map distance filter uses placeholder distance values until geocoding/radius search is implemented.
