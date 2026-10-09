# SAVJ Phase 2 — Domain and Data Foundation

Status: **Started**  
Working branch: `phase-2/domain-and-validation`  
Base: `phase-1/stabilize-and-flows`

## Goal

Move business rules out of the large dashboard component so the frontend can later use a real API without rewriting task logic. Keep the existing React + TypeScript + Vite stack and treat Lovable as a visual/flow reference only.

## Phase 2 work packages

1. **Domain rules** — central task status type, allowed transitions, and task-draft validation.
2. **UI integration** — use shared validation and transition rules in the current task-posting and task-detail flows.
3. **Automated checks** — add deterministic tests for valid/invalid transitions and task validation, then include them in CI.
4. **Persistence boundary** — define a small repository/service contract so browser-demo storage can be replaced by an API implementation.
5. **API readiness** — document endpoint contracts, authorization expectations, error format, and the persistence model before selecting a backend provider.

## Lifecycle rules

- Open → Accepted or Cancelled
- Accepted → In progress or Cancelled
- In progress → Awaiting approval or Cancelled
- Awaiting approval → Completed or back to In progress (for rework)
- Completed and Cancelled are terminal states

The UI's demo buttons do not enforce real identity, ownership, payment, proof upload, or server-side authorization. These rules are domain validation, not a security boundary until enforced by an API.

## Exit criteria

- Shared rules are imported by the app rather than duplicated in event handlers.
- Invalid transitions and invalid task drafts are covered by automated tests.
- CI runs build, typecheck, lint, and tests.
- Demo storage remains clearly separated from future server persistence.
- API and database choices are documented without committing credentials or pretending integrations exist.
