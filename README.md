# SAVJ 🌱

## Greener and Cleaner India.

SAVJ is a community-driven environmental platform designed to connect people who need local environmental tasks completed with suitable nearby workers, while enabling environmental drives, volunteering, skill-based opportunities, and impact tracking.

> **Community Engagement Project (CEP)** · **Environmental Sustainability & Community Engagement** · **Desktop-first Web Application**

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

- [x] Product concept and feature definition
- [x] Desktop-first UI direction
- [x] Onboarding flow
- [x] Task/worker requirements
- [x] Radius-based discovery concept
- [ ] Frontend implementation
- [ ] Backend/API
- [ ] Database
- [ ] Map integration
- [ ] Authentication and KYC workflow
- [ ] Task lifecycle
- [ ] Community module
- [ ] Testing
- [ ] Deployment

## Security

Never commit API keys, tokens, passwords, or private credentials. Use environment variables; see `.env.example`.

## Project

SAVJ is being developed as a Community Engagement Project by students of the Artificial Intelligence & Machine Learning department at ISBM College of Engineering, Pune.

**Greener and Cleaner India.** 🇮🇳🌱
