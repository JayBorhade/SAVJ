"""PostgreSQL-backed API smoke test run after Alembic migrations in CI."""
from __future__ import annotations

import os
import sys
import tempfile
from io import BytesIO
from pathlib import Path

from PIL import Image

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("JWT_SECRET", "test-secret-that-is-long-enough-for-local-tests")
os.environ.setdefault("SAVJ_UPLOAD_DIR", str(Path(tempfile.gettempdir()) / "savj-postgres-private-uploads"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from app.main import app


def register(client: TestClient, email: str, name: str, purpose: str = "Both") -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "test-password-123",
            "display_name": name,
            "locality": "Pune",
            "purpose": purpose,
            "skills": ["Cleanup"],
            "tools": ["Gloves"],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def upload_proof(client: TestClient, task_id: int, token: str, kind: str) -> None:
    buffer = BytesIO()
    Image.new("RGB", (4, 4), (25, 110, 60)).save(buffer, format="PNG")
    response = client.post(
        f"/api/v1/tasks/{task_id}/proofs/{kind}",
        headers=auth(token),
        files={"file": (f"{kind}.png", buffer.getvalue(), "image/png")},
    )
    assert response.status_code == 201, response.text


def main() -> None:
    upload_dir = Path(os.environ["SAVJ_UPLOAD_DIR"])
    upload_dir.mkdir(parents=True, exist_ok=True)
    with TestClient(app) as client:
        owner = register(client, "pg-owner@example.com", "Postgres Owner")
        worker = register(client, "pg-worker@example.com", "Postgres Worker", "Worker")
        outsider = register(client, "pg-outsider@example.com", "Postgres Outsider")

        created = client.post(
            "/api/v1/tasks",
            headers=auth(owner),
            json={
                "title": "PostgreSQL integration garden cleanup",
                "description": "Smoke test the production database path.",
                "category": "Gardening",
                "required_skills": ["Cleanup"],
                "required_tools": ["Gloves"],
                "location_text": "Pune",
                "budget_rupees": 250,
            },
        )
        assert created.status_code == 201, created.text
        task = created.json()
        task_id = task["id"]
        assert task["required_skills"] == ["Cleanup"] and task["required_tools"] == ["Gloves"]
        assert client.post(f"/api/v1/tasks/{task_id}/accept", headers=auth(worker)).status_code == 200
        assert client.get(f"/api/v1/tasks/{task_id}", headers=auth(outsider)).status_code == 404
        assert client.post(f"/api/v1/tasks/{task_id}/start", headers=auth(worker)).status_code == 200
        upload_proof(client, task_id, worker, "before")
        upload_proof(client, task_id, worker, "after")
        submitted = client.post(f"/api/v1/tasks/{task_id}/submit", headers=auth(worker))
        assert submitted.status_code == 200, submitted.text
        completed = client.post(f"/api/v1/tasks/{task_id}/approve", headers=auth(owner))
        assert completed.status_code == 200 and completed.json()["status"] == "Completed"
        rated = client.post(f"/api/v1/tasks/{task_id}/rating", headers=auth(owner), json={"score": 5, "comment": "Postgres smoke test"})
        assert rated.status_code == 201, rated.text
        workers = client.get("/api/v1/workers", headers=auth(owner)).json()
        worker_profile = next(item for item in workers if item["display_name"] == "Postgres Worker")
        assert worker_profile["rating_average"] == 5.0 and worker_profile["rating_count"] == 1
        assert any(item["notification_type"] == "task_completed" for item in client.get("/api/v1/me/notifications", headers=auth(worker)).json())

        drive = client.post(
            "/api/v1/drives",
            headers=auth(owner),
            json={"title": "Postgres Drive Smoke Test", "location_text": "Pune", "starts_at": "2030-10-10T07:30:00Z", "capacity": 1},
        )
        assert drive.status_code == 201, drive.text
        drive_id = drive.json()["id"]
        assert client.post(f"/api/v1/drives/{drive_id}/join", headers=auth(worker)).status_code == 201
        full = client.post(f"/api/v1/drives/{drive_id}/join", headers=auth(outsider))
        assert full.status_code == 409, full.text
        assert any(item["notification_type"] == "drive_joined" for item in client.get("/api/v1/me/notifications", headers=auth(owner)).json())

    print("PostgreSQL API smoke test passed: auth, task lifecycle, private proof, rating, notifications, and drive capacity.")


if __name__ == "__main__":
    main()
