# SAVJ 🌱

## Greener and Cleaner India.

SAVJ is a community-driven environmental platform designed to connect people who need local environmental tasks completed with suitable nearby workers, while enabling environmental drives, volunteering, skill-based opportunities, and impact tracking.

> **Community Engagement Project (CEP)** · **Environmental Sustainability & Community Engagement** · **Desktop-first Web Application**

## Run the full stack locally with Docker

Prerequisites: Docker Desktop with Compose enabled.

1. Copy the environment template: `Copy-Item .env.compose.example .env` (PowerShell) or `cp .env.compose.example .env` (macOS/Linux).
2. Edit `.env`. Replace both placeholders with different long random hex secrets. Do not use the example placeholders in a real environment.
3. Start the services: `docker compose up --build -d`.
4. Open the app at http://localhost:8080. The API documentation is available at http://localhost:8000/docs.
5. Check service health with `docker compose ps` and logs with `docker compose logs -f api web`.

Stop the stack with `docker compose down`. The named PostgreSQL and private-upload volumes persist. To deliberately delete local database and upload data, use `docker compose down -v`.

The API container runs migrations before startup, uses a non-root user, and stores proof images in a private volume rather than the frontend's public assets. This is a reproducible self-hosted starting point, not a complete managed production deployment: add HTTPS, managed secrets, off-site backups, monitoring, malware scanning, retention policy, and managed private object storage before accepting real users or sensitive documents.

## Overview

Local environmental problems often require coordination between citizens, skilled workers, volunteers, and community groups. SAVJ brings these interactions into one platform.

Users can:
- Post environmental tasks with photos, descriptions, budgets, skills, tools, location, and schedule.
- Discover nearby tasks using a configurable search radius.
- Join environmental community drives.
- Build profiles around skills, KYC verification, contributions, ratings, and impact.
- Submit before/after completion proof.
- Communicate through task-based messaging.
- Track environmental contributions such as volunteer hours, waste collected, and trees planted.

## Core Features

### 🌱 Environmental Tasks
Cleanup, gardening, waste collection, plantation, green-space, waterbody, and community-area tasks.

### 📍 Location & Radius Discovery
Workers choose a preferred radius. SAVJ displays eligible tasks within that distance and visualizes them on a map.

### 🛠️ Skill & Tool Requirements
Task creators define mandatory skills and tools. A worker can accept a task only when mandatory requirements are satisfied; otherwise the **Accept Task** action is disabled.

### 🪪 KYC & Trust
KYC verification supports safer paid/skilled work. Profiles can show verification, skills, ratings, and task history.

### 📸 Completion Proof
Workers submit before/after evidence. Requesters review and approve completed work.

### 🤝 Community Drives
Discover and join plantation drives, waterbody cleanups, waste collection, and neighborhood environmental activities.

### 🏆 Impact Tracking
Track tasks completed, volunteer hours, trees planted, waste collected, drives joined, and achievements.

## Key User Flows

**New user:**  
Splash → Welcome → Purpose → Location → Skills (worker) → KYC (if applicable) → Radius → Interests → Home

**Worker:**  
Explore → Radius → Task → Requirement Check → Accept → Chat → Complete → Proof → Approval → Rating

**Requester:**  
Post Task → Details → Requirements → Location → Review → Publish → Worker Accepts → Proof → Approval → Rating

**Volunteer:**  
Community → Drive → Details → Join → Participate → Impact Updated

## Product Design

SAVJ uses a desktop-first dashboard with:
- Forest-green navigation
- White/off-white content areas
- Natural green accents
- Rounded cards and subtle shadows
- Environmental imagery
- Map-based discovery
- Clear verification and status indicators

The product is intentionally positioned as an environmental community platform rather than a generic services marketplace.

## Planned Technology

The implementation stack may evolve, but the current direction includes:

- **Frontend:** React / TypeScript
- **Backend:** REST API
- **Database:** PostgreSQL
- **Geospatial:** PostgreSQL/PostGIS or equivalent
- **Maps:** Map API integration
- **Authentication:** Secure user authentication
- **Storage:** Image/document storage
- **Payments:** Future integration for paid tasks

## Repository Structure

```
src/
├── components/
├── pages/
├── layouts/
├── hooks/
├── services/
├── data/
└── types/

docs/
└── ARCHITECTURE.md
```

## Development Status

The integrated full-stack implementation is present on the stacked Phase 1–16 branches; these branches are not yet consolidated into `main` and the service is not deployed.

- [x] Desktop-first React/TypeScript frontend and onboarding
- [x] FastAPI API, SQLAlchemy models, authentication and profile
- [x] Task creation, discovery, lifecycle, worker directory and messaging APIs
- [x] Community drive and participation APIs
- [x] Private before/after proof upload and authorized retrieval
- [x] Radius-based task filtering and map UI
- [x] Alembic migration chain and Docker Compose files
- [x] Automated frontend/backend/container CI on the phase stack
- [x] Security audit, dependency audit, CodeQL and secret scanning workflows
- [x] Resolve the Phase 2 branch conflict and verify its CI
- [x] Commit `package-lock.json` and use `npm ci` for frontend CI/container builds
- [x] Use HttpOnly production access cookies, Origin checks, and server-side logout revocation
- [ ] Integrate the full phase stack into `main` in dependency order
- [ ] Add refresh-token rotation, email verification/password recovery, and MFA with configured providers
- [ ] Configure shared rate limiting, production object storage, malware scanning and retention
- [ ] Verify production hosting, HTTPS, secrets, backups, monitoring and logs
- [ ] Complete browser end-to-end, staging DAST and independent penetration testing

## Security

Never commit API keys, tokens, passwords, or private credentials. Use environment variables; see `.env.example`.

## Project

SAVJ is being developed as a Community Engagement Project by students of the Artificial Intelligence & Machine Learning department at ISBM College of Engineering, Pune.

**Greener and Cleaner India.** 🇮🇳🌱


## Current implementation note

The complete implementation is organized as stacked branches from `phase-1/stabilize-and-flows` through `phase-16/launch-hardening`, with a documentation-only Phase 17 verification branch and security PR #18 targeting Phase 16. Later-phase backend, database, API integration, task lifecycle, community drives, messaging, proof uploads, geospatial discovery, worker directory, map UI, Docker, and security hardening exist on the phase stack; they are not yet integrated into `main` or deployed.

Important limitations: Phase 2's merge conflict has been resolved in its branch and CI passed, but the stacked phase PRs are still open and the implementation is not yet consolidated into `main`. A committed `package-lock.json` now exists, and frontend CI/container builds use `npm ci`. Production builds use HttpOnly access cookies with Origin checks and logout revocation; refresh-token rotation, email verification/password recovery, and MFA are not yet implemented. Login/register throttling is process-local, and production object storage, malware scanning, shared rate limiting, monitoring, backup/restore verification, browser end-to-end testing, and independent security testing remain release gates. The dashboard retains demo-mode/sample content when not connected to the backend. See [implementation status](docs/IMPLEMENTATION_STATUS.md) and [security audit](docs/SECURITY_AUDIT.md) for the current checklist.
