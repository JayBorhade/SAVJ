# SAVJ Phase 2 — Domain and Data Foundation

Status: **Phase 2 implementation and CI verification complete**  
Working branch: `phase-2/domain-and-validation`  
Base: `phase-1/stabilize-and-flows`

## Delivered in this branch

- Shared task status types and an explicit transition table.
- Shared validation for task title, location, budget and optional schedule.
- Existing task-posting and task-detail actions now call the shared domain rules.
- A `TaskRepository` contract and browser-local-storage adapter, with task load/save/create routed through that boundary.
- Automated Node test cases for allowed transitions, rejected jumps, terminal states, cancellation, valid budgets and invalid drafts.
- Repository adapter tests for empty storage, task record round-tripping, malformed JSON handling and default descriptions.
- CI steps for automated tests, typecheck, lint and production build.
- Provider-neutral API/data contract covering users, tasks, task requirements, proof metadata, community drives, participation, messages and impact events.

## Lifecycle rules

- Open → Accepted or Cancelled
- Accepted → In progress or Cancelled
- In progress → Awaiting approval or Cancelled
- Awaiting approval → Completed or back to In progress (for rework)
- Completed and Cancelled are terminal states

These are domain/UI rules only. They do not provide security until the API enforces authorization and transitions on the server.

## Verification checklist

- [x] Shared domain rules are imported by the app.
- [x] Task form uses shared validation.
- [x] Demo task persistence uses the repository adapter.
- [x] Automated domain and repository-adapter tests are included in the repository.
- [x] CI configuration includes test, typecheck, lint and build steps.
- [x] API and data contract is documented.
- [x] GitHub Actions reports passing test, typecheck, lint and build jobs (run 37887981182).
- [ ] Review runtime behavior against the Lovable reference.

## Explicitly out of scope / not yet implemented

- Production API or database.
- Authentication, sessions, KYC or server authorization.
- Real image upload/storage and requester approval.
- Payments, live maps/geocoding, real-time messaging and notifications.
- Verified environmental impact accounting.

The localStorage adapter is a replaceable demo adapter, not multi-user persistence. Select production providers only after deployment and credential requirements are confirmed.
