# Phase 8 — Geospatial task discovery

## Delivered
- Add optional latitude/longitude fields to tasks with validation and database indexes.
- Add an explicit, idempotent migration for older task tables that do not yet contain coordinates.
- Add radius-filtered API search with bounding-box candidate reduction and Haversine distance validation.
- Add browser geolocation opt-in, distance calculation, and an explicit action to tag a new task with the current coordinates.
- Query the backend by latitude, longitude and selected radius when location is enabled; tasks without coordinates are excluded from live radius results.

## Limitations
- This phase does not include live map tiles or geocoding from free-text addresses. A map provider and key are required for a real interactive map.
- Browser geolocation requires permission and a secure context (localhost or HTTPS). Users can continue browsing without it.
- Radius results only include tasks with stored coordinates; older tasks without coordinates remain discoverable by text when location filtering is off.
