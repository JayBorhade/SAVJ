import os
import tempfile

_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_db_file.close()
os.environ["DATABASE_URL"] = "sqlite:///" + _db_file.name
os.environ["JWT_SECRET"] = "test-secret-that-is-long-enough-for-local-tests"
os.environ["APP_ENV"] = "test"

from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
client = TestClient(app)

def register(email: str, name: str, purpose: str = "Both") -> tuple[str, dict]:
    response = client.post("/api/v1/auth/register", json={"email":email,"password":"test-password-123","display_name":name,"locality":"Pune","purpose":purpose,"skills":["Cleanup"]})
    assert response.status_code == 201, response.text
    body = response.json()
    return body["access_token"], body["user"]

def auth(token: str) -> dict[str, str]:
    return {"Authorization":"Bearer " + token}

def test_health_auth_and_duplicate_email():
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/api/v1/me").status_code == 401
    token, user = register("requester@example.com","Requester")
    assert client.get("/api/v1/me",headers=auth(token)).json()["id"] == user["id"]
    assert client.post("/api/v1/auth/register",json={"email":"requester@example.com","password":"test-password-123","display_name":"Duplicate"}).status_code == 409
    assert client.post("/api/v1/auth/login",json={"email":"requester@example.com","password":"test-password-123"}).status_code == 200
    assert client.post("/api/v1/auth/login",json={"email":"requester@example.com","password":"wrong-password"}).status_code == 401

def test_task_lifecycle_permissions_and_impact():
    requester_token, _ = register("owner@example.com","Owner")
    worker_token, worker = register("worker@example.com","Worker")
    created = client.post("/api/v1/tasks",json={"title":"Clean community garden","description":"Collect litter","location_text":"Pune","budget_rupees":500},headers=auth(requester_token))
    assert created.status_code == 201, created.text
    task = created.json()
    assert task["budget_minor_units"] == 50000
    assert client.post(f"/api/v1/tasks/{task['id']}/accept",headers=auth(requester_token)).status_code == 403
    accepted = client.post(f"/api/v1/tasks/{task['id']}/accept",headers=auth(worker_token))
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["worker_id"] == worker["id"]
    assert client.post(f"/api/v1/tasks/{task['id']}/start",headers=auth(worker_token)).status_code == 200
    assert client.post(f"/api/v1/tasks/{task['id']}/submit",headers=auth(worker_token)).status_code == 200
    assert client.post(f"/api/v1/tasks/{task['id']}/approve",headers=auth(worker_token)).status_code == 403
    completed = client.post(f"/api/v1/tasks/{task['id']}/approve",headers=auth(requester_token))
    assert completed.status_code == 200 and completed.json()["status"] == "Completed"
    assert client.get("/api/v1/me/impact",headers=auth(worker_token)).json()["verified_completed_tasks"] == 1

def test_drives_and_task_scoped_messages():
    owner_token, _ = register("driveowner@example.com","Drive Owner")
    attendee_token, _ = register("attendee@example.com","Attendee")
    drive = client.post("/api/v1/drives",headers=auth(owner_token),json={"title":"Pune Lake Cleanup","description":"Bring gloves","location_text":"Pashan Lake","starts_at":"2030-10-10T07:30:00Z","capacity":2})
    assert drive.status_code == 201, drive.text
    drive_id = drive.json()["id"]
    assert client.post(f"/api/v1/drives/{drive_id}/join",headers=auth(attendee_token)).json()["status"] == "joined"
    assert client.post(f"/api/v1/drives/{drive_id}/join",headers=auth(attendee_token)).json()["status"] == "already_joined"
    task = client.post("/api/v1/tasks",headers=auth(owner_token),json={"title":"Garden cleanup","location_text":"Pune","budget_rupees":0}).json()
    assert client.get(f"/api/v1/tasks/{task['id']}/messages",headers=auth(attendee_token)).status_code == 403
    assert client.get(f"/api/v1/tasks/{task['id']}/messages",headers=auth(owner_token)).status_code == 200


def test_private_task_proof_upload_permissions_and_validation(tmp_path, monkeypatch):
    from app import main as main_module
    monkeypatch.setattr(main_module, "UPLOAD_DIR", tmp_path / "private-proof-files")
    requester_token, _ = register("proofowner@example.com", "Proof Owner")
    worker_token, worker = register("proofworker@example.com", "Proof Worker")
    outsider_token, _ = register("proofoutsider@example.com", "Proof Outsider")
    task = client.post("/api/v1/tasks", headers=auth(requester_token), json={
        "title": "Clean garden beds", "location_text": "Pune", "budget_rupees": 100
    }).json()
    task_id = task["id"]
    assert client.post(f"/api/v1/tasks/{task_id}/accept", headers=auth(worker_token)).status_code == 200
    assert client.post(f"/api/v1/tasks/{task_id}/start", headers=auth(worker_token)).status_code == 200
    image_bytes = b"\\x89PNG\\r\\n\\x1a\\n" + b"test-image-payload"
    uploaded = client.post(f"/api/v1/tasks/{task_id}/proofs/before", headers=auth(worker_token),
                           files={"file": ("before.png", image_bytes, "image/png")})
    assert uploaded.status_code == 201, uploaded.text
    proof = uploaded.json()
    assert proof["proof_kind"] == "before"
    assert proof["content_type"] == "image/png"
    assert not (tmp_path / "public" / proof["original_name"]).exists()
    assert client.get(f"/api/v1/tasks/{task_id}/proofs", headers=auth(requester_token)).json()[0]["id"] == proof["id"]
    assert client.get(f"/api/v1/proofs/{proof['id']}/content", headers=auth(requester_token)).content == image_bytes
    assert client.get(f"/api/v1/proofs/{proof['id']}/content", headers=auth(outsider_token)).status_code == 403
    invalid = client.post(f"/api/v1/tasks/{task_id}/proofs/after", headers=auth(worker_token),
                          files={"file": ("fake.png", b"not an image", "image/png")})
    assert invalid.status_code == 415
    assert client.post(f"/api/v1/tasks/{task_id}/proofs/unknown", headers=auth(worker_token),
                       files={"file": ("before.png", image_bytes, "image/png")}).status_code == 422


def test_radius_discovery_uses_task_coordinates():
    owner_token, _ = register("geoowner@example.com", "Geo Owner")
    headers = auth(owner_token)
    near = client.post("/api/v1/tasks", headers=headers, json={
        "title": "Nearby cleanup", "location_text": "Pune", "budget_rupees": 0,
        "latitude": 18.5204, "longitude": 73.8567
    })
    far = client.post("/api/v1/tasks", headers=headers, json={
        "title": "Far cleanup", "location_text": "Mumbai", "budget_rupees": 0,
        "latitude": 19.0760, "longitude": 72.8777
    })
    assert near.status_code == 201, near.text
    assert far.status_code == 201, far.text
    found = client.get("/api/v1/tasks", headers=headers, params={
        "latitude": 18.5204, "longitude": 73.8567, "radius_km": 5
    })
    assert found.status_code == 200, found.text
    assert [item["title"] for item in found.json()] == ["Nearby cleanup"]
    assert client.get("/api/v1/tasks", headers=headers, params={"latitude": 18.5}).status_code == 422
    assert client.get("/api/v1/tasks", headers=headers, params={"radius_km": 5}).status_code == 422
    invalid = client.post("/api/v1/tasks", headers=headers, json={
        "title": "Invalid coordinates", "location_text": "Pune", "budget_rupees": 0,
        "latitude": 100, "longitude": 73
    })
    assert invalid.status_code == 422


def test_worker_directory_filters_skills_without_exposing_email():
    worker_token, worker = register("publicworker@example.com", "Garden Helper", purpose="Worker")
    assert client.patch("/api/v1/me", headers=auth(worker_token), json={"skills": ["Gardening", "Cleanup"]}).status_code == 200
    requester_token, _ = register("private.requester@example.com", "Task Requester", purpose="Requester")
    all_workers = client.get("/api/v1/workers", headers=auth(requester_token))
    assert all_workers.status_code == 200, all_workers.text
    matching = [item for item in all_workers.json() if item["id"] == worker["id"]]
    assert len(matching) == 1
    assert "email" not in matching[0]
    assert client.get("/api/v1/workers", headers=auth(requester_token), params={"skill": "garden"}).json()[0]["id"] == worker["id"]
    assert client.get("/api/v1/workers", headers=auth(requester_token), params={"search": "Task Requester"}).json() == []
