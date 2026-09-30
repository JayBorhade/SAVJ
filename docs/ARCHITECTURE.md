# SAVJ Architecture

## Product Architecture

SAVJ is planned as a desktop-first web application with a modular frontend, API layer, database, geospatial services, storage, and external integrations.

```
Web App
  │
  ├── Onboarding / Auth
  ├── Tasks / Workers
  ├── Community
  ├── Messages
  └── Profiles / Impact
          │
       REST API
          │
   ┌──────┼────────┐
   │      │        │
Database  Maps   Storage
   │      │        │
   └──────┼────────┘
          │
    Trust & Workflow
   KYC · Proof · Ratings
```

## Core Modules

### Identity & Onboarding
Purpose selection, location preference, worker skills, applicable KYC state, task radius, and environmental interests.

### Task Management
Task creation, discovery, acceptance, status changes, completion proof, approval, and ratings.

### Requirement Validation
Mandatory requirements can include:
- Required skills
- Required tools
- Applicable KYC status
- Worker search radius

The **Accept Task** action is enabled only when mandatory requirements are satisfied.

### Geospatial Discovery
The Explore interface combines a task list with a map. The selected worker radius controls which tasks are displayed.

### Community
Environmental drives can be published, discovered, joined, and tracked.

### Impact
Completed work and community participation update environmental impact metrics and achievements.

## External Integrations

Potential integrations:
- Map/geocoding provider
- Authentication provider
- Image/document storage
- Payment provider

All secrets must be supplied through environment variables and excluded from version control.

## Design Principle

Keep the application modular and replaceable. External services should be isolated behind service interfaces so providers can change without rewriting core product logic.
