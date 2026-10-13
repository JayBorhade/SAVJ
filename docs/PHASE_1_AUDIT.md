# SAVJ Phase 1 — Codebase Audit & Stabilization

Date: 2026-10-09
Branch: `phase-1/stabilize-and-flows`
Reference UI: https://savj.lovable.app
Implementation repository: https://github.com/JayBorhade/SAVJ

## Source-of-truth decision

Lovable is the visual and interaction reference only. The GitHub repository is the implementation source of truth. Do not copy the Lovable application's generated code wholesale or overwrite the repository with it. Recreate its onboarding, task creation, discovery, task lifecycle, community, profile, messaging and impact flows in the existing React + TypeScript + Vite app, preserving the forest-green visual system.

## Confirmed current state

- React + TypeScript + Vite frontend exists.
- Forest-green desktop-first dashboard and responsive sidebar exist.
- Dashboard has sample tasks, search, category/radius filters, community-drive join state and a task-posting modal.
- Some interactions use in-memory React state only; refresh loses changes.
- The map is illustrative, not a live geospatial map.
- Authentication, real KYC, server-side eligibility enforcement, durable task lifecycle, messaging, upload storage, payments and production persistence are not implemented.
- Current CI workflow runs `npm install` and `npm run build`; test and lint checks are not currently in the CI workflow.
- Demo/sample metrics and scheduled drives must be labelled as sample data rather than presented as verified real-world impact.

## Phase 1 exit criteria

- [ ] Map all routes/screens and primary click paths against the Lovable reference.
- [ ] Add explicit demo-data messaging and remove unsupported claims.
- [ ] Implement a guided onboarding flow that captures the user's name, role/purpose, area, skills when relevant, radius and interests.
- [ ] Ensure the entered name and area drive the greeting and location chip.
- [ ] Validate task creation fields, non-negative budget and required schedule/location.
- [ ] Make task cards open a task-detail view and clearly separate demo actions from server-backed actions.
- [ ] Define and enforce legal task status transitions; require before AND after completion proof before approval.
- [ ] Prevent the UI from claiming identity verification, payments, or persistence unless a real service is integrated.
- [ ] Add automated tests for core validation and lifecycle rules.
- [ ] Run production build, typecheck, lint and tests; record actual results.
- [ ] Review responsive layout, keyboard access, focus states and empty/error states.

## Implementation sequence

1. Stabilize foundation and shared data/types.
2. Onboarding and identity-aware shell.
3. Task creation, details, requirements and worker lifecycle.
4. Community drives and participation.
5. Messages, profile, KYC states and impact.
6. Persistence/API, authorization and geospatial integrations.
7. Automated tests, security review and deployment.

## Engineering guardrails

- Keep secrets out of Git; use environment variables.
- Do not represent mock authentication as real authentication.
- Do not mark KYC as verified from a file selection or client-side action.
- Never credit environmental impact from an unapproved or cancelled task.
- Do not call a task accepted/completed unless the corresponding transition succeeds.
- Preserve the current design direction and use Lovable only as a visual/flow reference.
