# SAVJ API and Data Contract (Draft)

This document defines a provider-neutral contract for the future backend. It is not evidence that an API or database has been deployed.

## Conventions

- Base path: `/api/v1`
- JSON request and response bodies.
- IDs are opaque strings at the API boundary; the current browser demo uses numeric IDs.
- Timestamps use ISO 8601 UTC.
- Authenticated endpoints require a verified session; the server derives the acting user ID from that session rather than trusting a user ID in the request body.
- Validate all inputs on the server. Client-side validation is usability only.
- Use pagination for list endpoints and a consistent error envelope.

## Error envelope

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid fields.",
    "fields": { "title": "Enter a task title." },
    "requestId": "opaque-request-id"
  }
}
```

Do not return secrets, stack traces, or private KYC documents in errors.

## Proposed endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/me` | Current user's profile and participation preferences |
| PATCH | `/api/v1/me` | Update profile, locality, radius and skills |
| GET | `/api/v1/tasks` | Discover tasks using radius/category/status filters |
| POST | `/api/v1/tasks` | Create a task as the authenticated requester |
| GET | `/api/v1/tasks/{taskId}` | Fetch task details |
| POST | `/api/v1/tasks/{taskId}/accept` | Accept an eligible open task |
| POST | `/api/v1/tasks/{taskId}/start` | Move an accepted task to in progress |
| POST | `/api/v1/tasks/{taskId}/proof` | Register uploaded before/after proof references |
| POST | `/api/v1/tasks/{taskId}/approve` | Requester approves completion |
| POST | `/api/v1/tasks/{taskId}/cancel` | Cancel when permitted by policy |
| GET | `/api/v1/drives` | Discover community drives |
| POST | `/api/v1/drives/{driveId}/join` | Join a drive idempotently |
| GET | `/api/v1/me/impact` | Calculate impact from eligible completed activity |
| GET | `/api/v1/tasks/{taskId}/messages` | Read a task conversation |
| POST | `/api/v1/tasks/{taskId}/messages` | Send a task conversation message |

## Core data model

- **User**: id, displayName, locality, coordinates (optional), radiusKm, purpose, skills, createdAt, updatedAt.
- **Task**: id, requesterId, workerId (nullable), title, description, category, locationText, coordinates (nullable), budgetMinorUnits, currency, scheduledAt (nullable), status, createdAt, updatedAt, version.
- **TaskRequirement**: id, taskId, requirementType, requirementValue, required.
- **TaskProof**: id, taskId, uploadedBy, kind (`before` or `after`), storageKey, contentType, sizeBytes, createdAt.
- **CommunityDrive**: id, organizerId, title, description, locationText, coordinates (nullable), startsAt, endsAt (nullable), capacity (nullable), status.
- **DriveParticipation**: id, driveId, userId, status, joinedAt; unique constraint on (driveId, userId).
- **Message**: id, taskId, senderId, body, createdAt, readAt (nullable).
- **ImpactEvent**: id, userId, taskId or driveId, eventType, quantity (nullable), unit (nullable), verifiedAt (nullable), createdAt.

## Invariants and security

1. The API enforces the same task transitions as `src/domain/taskWorkflow.ts`.
2. Only the task requester can approve completion; only eligible users can accept an open task.
3. Status changes use a database transaction and optimistic concurrency (version/ETag) to avoid double acceptance.
4. A task cannot become Completed until required proof has uploaded successfully and the requester approves it.
5. File uploads use signed, short-lived upload URLs; validate content type, size and file signatures. Never trust client filenames.
6. KYC documents and verification state are private; clients cannot self-mark as verified.
7. Impact is computed from verified/approved records, never from browser-supplied counters.
8. Store money as integer minor units with explicit currency. Never use floating point as the authoritative payment amount.
9. Rate-limit writes, protect against duplicate submissions, audit sensitive changes, and scope every task/message query by authorization.
10. Keep secrets in deployment environment variables and never commit them.

## Integration strategy

Implement a server-side repository/API adapter behind the frontend service boundary. Keep the localStorage adapter strictly for demos. Select the production database, auth provider, map provider, and object storage in a separate integration decision once deployment constraints and keys are available.
