import os
import stat
import tempfile
from io import BytesIO
from PIL import Image

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

def test_api_rejects_naive_or_past_schedules_and_blank_profile_fields():
    token, _ = register("schedule-validation@example.com", "Schedule Validation")
    headers = auth(token)
    base_task = {"title": "Scheduled cleanup", "location_text": "Pune", "budget_rupees": 100}
    naive_task = client.post(
        "/api/v1/tasks", headers=headers,
        json={**base_task, "scheduled_at": "2030-10-10T07:30:00"},
    )
    assert naive_task.status_code == 422
    past_task = client.post(
        "/api/v1/tasks", headers=headers,
        json={**base_task, "scheduled_at": "2000-10-10T07:30:00Z"},
    )
    assert past_task.status_code == 422
    naive_drive = client.post(
        "/api/v1/drives", headers=headers,
        json={"title": "Future cleanup", "location_text": "Pune", "starts_at": "2030-10-10T07:30:00"},
    )
    assert naive_drive.status_code == 422
    past_drive = client.post(
        "/api/v1/drives", headers=headers,
        json={"title": "Past cleanup", "location_text": "Pune", "starts_at": "2000-10-10T07:30:00Z"},
    )
    assert past_drive.status_code == 422
    assert client.patch("/api/v1/me", headers=headers, json={"display_name": "   "}).status_code == 422
    assert client.patch("/api/v1/me", headers=headers, json={"skills": ["x" * 81]}).status_code == 422


def test_logout_revokes_previous_access_tokens():
    token, _ = register("logout@example.com", "Logout User")
    assert client.get("/api/v1/me", headers=auth(token)).status_code == 200
    response = client.post("/api/v1/auth/logout", headers=auth(token))
    assert response.status_code == 204
    assert client.get("/api/v1/me", headers=auth(token)).status_code == 401


def test_production_auth_uses_secure_cookie_and_origin_checks(monkeypatch):
    from app import main as main_module

    register("cookie@example.com", "Cookie User")
    monkeypatch.setattr(main_module, "_PRODUCTION", True)
    monkeypatch.setattr(main_module.settings, "app_env", "production")
    monkeypatch.setattr(main_module.settings, "cors_origins", "https://app.example.com")
    secure_client = TestClient(app, base_url="https://testserver")
    secure_client.cookies.clear()
    try:
        response = secure_client.post(
            "/api/v1/auth/login",
            json={"email": "cookie@example.com", "password": "test-password-123"},
        )
        assert response.status_code == 200, response.text
        assert response.json()["access_token"] is None
        set_cookie = response.headers.get("set-cookie", "")
        assert "HttpOnly" in set_cookie and "Secure" in set_cookie and "SameSite=lax" in set_cookie
        denied = secure_client.post("/api/v1/auth/logout")
        assert denied.status_code == 403
        me = secure_client.get(
            "/api/v1/me",
            headers={"Origin": "https://app.example.com"},
        )
        assert me.status_code == 200, me.text
        logout = secure_client.post(
            "/api/v1/auth/logout",
            headers={"Origin": "https://app.example.com"},
        )
        assert logout.status_code == 204
        assert secure_client.get("/api/v1/me").status_code == 401
    finally:
        secure_client.cookies.clear()
        secure_client.close()
        monkeypatch.setattr(main_module, "_PRODUCTION", False)
        monkeypatch.setattr(main_module.settings, "app_env", "test")
        monkeypatch.setattr(main_module.settings, "cors_origins", "http://localhost:5173,http://127.0.0.1:5173")


def test_task_creation_rate_limit_returns_429():
    from app import main as main_module

    token, _ = register("task-limit@example.com", "Task Limit")
    original_env = main_module.settings.app_env
    main_module.settings.app_env = "development"
    main_module._auth_attempts.clear()
    try:
        for _ in range(10):
            response = client.post("/api/v1/tasks", headers=auth(token), json={})
            assert response.status_code == 422
        limited = client.post("/api/v1/tasks", headers=auth(token), json={})
        assert limited.status_code == 429
        assert "retry-after" in limited.headers
    finally:
        main_module._auth_attempts.clear()
        main_module.settings.app_env = original_env


def test_email_verification_and_password_reset_tokens_are_single_use(monkeypatch):
    from app import main as main_module

    sent = []
    monkeypatch.setattr(main_module, "_PRODUCTION", True)
    monkeypatch.setattr(main_module, "_send_action_email", lambda recipient, purpose, token: sent.append((recipient, purpose, token)))
    client.cookies.clear()
    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": "verify-flow@example.com", "password": "test-password-123",
              "display_name": "Verify Flow", "locality": "Pune", "purpose": "Both"},
    )
    assert register_response.status_code == 201, register_response.text
    assert register_response.json()["requires_email_verification"] is True
    assert register_response.json()["access_token"] is None
    assert client.post(
        "/api/v1/auth/login",
        json={"email": "verify-flow@example.com", "password": "test-password-123"},
    ).status_code == 403

    verify_token = sent[-1][2]
    verified = client.post("/api/v1/auth/verify-email", json={"token": verify_token})
    assert verified.status_code == 200
    assert client.post("/api/v1/auth/verify-email", json={"token": verify_token}).status_code == 400
    assert client.post(
        "/api/v1/auth/login",
        json={"email": "verify-flow@example.com", "password": "test-password-123"},
    ).status_code == 200

    reset_request = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "verify-flow@example.com"},
    )
    assert reset_request.status_code == 202
    assert "verify-flow@example.com" not in reset_request.text
    reset_token = sent[-1][2]
    reset = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": reset_token, "new_password": "new-test-password-456"},
    )
    assert reset.status_code == 200
    assert client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": reset_token, "new_password": "another-password-789"},
    ).status_code == 400
    assert client.post(
        "/api/v1/auth/login",
        json={"email": "verify-flow@example.com", "password": "test-password-123"},
    ).status_code == 401
    assert client.post(
        "/api/v1/auth/login",
        json={"email": "verify-flow@example.com", "password": "new-test-password-456"},
    ).status_code == 200
    client.cookies.clear()


def test_task_acceptance_enforces_required_skills_and_tools():
    owner_token, _ = register("requirements-owner@example.com", "Requirements Owner")
    worker_token, worker = register("requirements-worker@example.com", "Requirements Worker", "Worker")
    response = client.post(
        "/api/v1/tasks",
        headers=auth(owner_token),
        json={"title": "Prepare garden beds", "location_text": "Pune", "budget_rupees": 300,
              "required_skills": ["Gardening"], "required_tools": ["Shovel"]},
    )
    assert response.status_code == 201, response.text
    task = response.json()
    assert task["required_skills"] == ["Gardening"]
    assert task["required_tools"] == ["Shovel"]
    assert client.post(f"/api/v1/tasks/{task['id']}/accept", headers=auth(worker_token)).status_code == 409
    updated = client.patch(
        "/api/v1/me",
        headers=auth(worker_token),
        json={"skills": ["Cleanup", "Gardening"], "tools": ["Shovel"]},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["tools"] == ["Shovel"]
    accepted = client.post(f"/api/v1/tasks/{task['id']}/accept", headers=auth(worker_token))
    assert accepted.status_code == 200, accepted.text


def test_task_lifecycle_permissions_and_impact(tmp_path, monkeypatch):
    from app import main as main_module
    monkeypatch.setattr(main_module, "UPLOAD_DIR", tmp_path / "task-proof-files")

    def upload_pair(task_id: int, token: str) -> None:
        for kind in ("before", "after"):
            buffer = BytesIO()
            Image.new("RGB", (2, 2), (40, 120, 60)).save(buffer, format="PNG")
            response = client.post(
                f"/api/v1/tasks/{task_id}/proofs/{kind}",
                headers=auth(token),
                files={"file": (f"{kind}.png", buffer.getvalue(), "image/png")},
            )
            assert response.status_code == 201, response.text

    requester_token, _ = register("owner@example.com","Owner")
    worker_token, worker = register("worker@example.com","Worker")
    outsider_token, _ = register("taskoutsider@example.com","Outsider")
    created = client.post("/api/v1/tasks",json={"title":"Clean community garden","description":"Collect litter","location_text":"Pune","private_location_text":"42 Secret Lane, Pune","latitude":18.5204,"longitude":73.8567,"budget_rupees":500},headers=auth(requester_token))
    assert created.status_code == 201, created.text
    task = created.json()
    assert task["budget_minor_units"] == 50000
    # Open tasks are discoverable, but private task details are hidden after acceptance.
    open_detail = client.get(f"/api/v1/tasks/{task['id']}",headers=auth(outsider_token))
    assert open_detail.status_code == 200
    assert open_detail.json()["private_location_text"] is None
    assert open_detail.json()["latitude"] == 18.52 and open_detail.json()["longitude"] == 73.86
    open_list = client.get("/api/v1/tasks",headers=auth(outsider_token),params={"status":"Open"}).json()
    listed_task = next(item for item in open_list if item["id"] == task["id"])
    assert listed_task["private_location_text"] is None and listed_task["latitude"] == 18.52
    assert client.post(f"/api/v1/tasks/{task['id']}/accept",headers=auth(requester_token)).status_code == 403
    accepted = client.post(f"/api/v1/tasks/{task['id']}/accept",headers=auth(worker_token))
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["worker_id"] == worker["id"]
    assert client.get(f"/api/v1/tasks/{task['id']}",headers=auth(worker_token)).json()["private_location_text"] == "42 Secret Lane, Pune"
    assert client.get(f"/api/v1/tasks/{task['id']}",headers=auth(requester_token)).json()["private_location_text"] == "42 Secret Lane, Pune"
    assert any(n["notification_type"] == "task_accepted" for n in client.get("/api/v1/me/notifications",headers=auth(requester_token)).json())
    assert client.post(f"/api/v1/tasks/{task['id']}/accept",headers=auth(outsider_token)).status_code == 409
    assert client.get(f"/api/v1/tasks/{task['id']}",headers=auth(outsider_token)).status_code == 404
    outsider_tasks = client.get("/api/v1/tasks",headers=auth(outsider_token),params={"status":"Accepted"})
    assert outsider_tasks.status_code == 200
    assert all(item["id"] != task["id"] for item in outsider_tasks.json())
    assert client.post(f"/api/v1/tasks/{task['id']}/start",headers=auth(worker_token)).status_code == 200
    assert any(n["notification_type"] == "task_started" for n in client.get("/api/v1/me/notifications",headers=auth(requester_token)).json())
    assert client.post(f"/api/v1/tasks/{task['id']}/submit",headers=auth(worker_token)).status_code == 409
    upload_pair(task["id"], worker_token)
    assert stat.S_IMODE(main_module.UPLOAD_DIR.stat().st_mode) == 0o700
    assert all(stat.S_IMODE(path.stat().st_mode) == 0o600 for path in main_module.UPLOAD_DIR.iterdir() if path.is_file())
    assert client.post(f"/api/v1/tasks/{task['id']}/submit",headers=auth(worker_token)).status_code == 200
    assert any(n["notification_type"] == "task_submitted" for n in client.get("/api/v1/me/notifications",headers=auth(requester_token)).json())
    # Requesters can ask for rework; a new proof pair is required for resubmission.
    rework = client.post(f"/api/v1/tasks/{task['id']}/start",headers=auth(requester_token))
    assert rework.status_code == 200 and rework.json()["status"] == "In progress"
    assert any(n["notification_type"] == "task_rework" for n in client.get("/api/v1/me/notifications",headers=auth(worker_token)).json())
    assert client.post(f"/api/v1/tasks/{task['id']}/submit",headers=auth(worker_token)).status_code == 409
    upload_pair(task["id"], worker_token)
    assert client.post(f"/api/v1/tasks/{task['id']}/submit",headers=auth(worker_token)).status_code == 200
    assert client.post(f"/api/v1/tasks/{task['id']}/approve",headers=auth(worker_token)).status_code == 403
    completed = client.post(f"/api/v1/tasks/{task['id']}/approve",headers=auth(requester_token))
    assert completed.status_code == 200 and completed.json()["status"] == "Completed"
    assert any(n["notification_type"] == "task_completed" for n in client.get("/api/v1/me/notifications",headers=auth(worker_token)).json())
    assert client.post(f"/api/v1/tasks/{task['id']}/approve",headers=auth(requester_token)).status_code == 409
    assert client.get("/api/v1/me/impact",headers=auth(worker_token)).json()["verified_completed_tasks"] == 1
    rating_response = client.post(
        f"/api/v1/tasks/{task['id']}/rating",
        headers=auth(requester_token),
        json={"score": 5, "comment": "Reliable and careful work."},
    )
    assert rating_response.status_code == 201, rating_response.text
    assert client.get(f"/api/v1/tasks/{task['id']}/rating",headers=auth(requester_token)).json()["score"] == 5
    assert client.post(f"/api/v1/tasks/{task['id']}/rating",headers=auth(requester_token),json={"score": 4}).status_code == 409
    assert client.post(f"/api/v1/tasks/{task['id']}/rating",headers=auth(worker_token),json={"score": 5}).status_code == 404
    worker_rows = client.get("/api/v1/workers",headers=auth(requester_token)).json()
    worker_row = next(item for item in worker_rows if item["id"] == worker["id"])
    assert worker_row["rating_average"] == 5.0 and worker_row["rating_count"] == 1
    requester_notifications = client.get("/api/v1/me/notifications",headers=auth(requester_token)).json()
    assert client.get("/api/v1/me/notifications",headers=auth(outsider_token)).json() == []
    unread = next((item for item in requester_notifications if item["read_at"] is None), None)
    if unread:
        marked = client.post(f"/api/v1/me/notifications/{unread['id']}/read",headers=auth(requester_token))
        assert marked.status_code == 200 and marked.json()["read_at"] is not None
    read_all = client.post("/api/v1/me/notifications/read-all",headers=auth(requester_token))
    assert read_all.status_code == 200 and read_all.json()["updated"] >= 0

def test_drives_and_task_scoped_messages():
    owner_token, _ = register("driveowner@example.com","Drive Owner")
    attendee_token, _ = register("attendee@example.com","Attendee")
    drive = client.post("/api/v1/drives",headers=auth(owner_token),json={"title":"Pune Lake Cleanup","description":"Bring gloves","location_text":"Pashan Lake","starts_at":"2030-10-10T07:30:00Z","capacity":2})
    assert drive.status_code == 201, drive.text
    drive_id = drive.json()["id"]
    assert client.post(f"/api/v1/drives/{drive_id}/join",headers=auth(attendee_token)).json()["status"] == "joined"
    assert any(n["notification_type"] == "drive_joined" for n in client.get("/api/v1/me/notifications",headers=auth(owner_token)).json())
    assert client.post(f"/api/v1/drives/{drive_id}/join",headers=auth(attendee_token)).json()["status"] == "already_joined"
    second_token, _ = register("secondattendee@example.com","Second Attendee")
    third_token, _ = register("thirdattendee@example.com","Third Attendee")
    assert client.post(f"/api/v1/drives/{drive_id}/join",headers=auth(second_token)).json()["status"] == "joined"
    full = client.post(f"/api/v1/drives/{drive_id}/join",headers=auth(third_token))
    assert full.status_code == 409
    task = client.post("/api/v1/tasks",headers=auth(owner_token),json={"title":"Garden cleanup","location_text":"Pune","budget_rupees":0}).json()
    assert client.get(f"/api/v1/tasks/{task['id']}/messages",headers=auth(attendee_token)).status_code == 403
    assert client.post(f"/api/v1/tasks/{task['id']}/accept",headers=auth(attendee_token)).status_code == 200
    assert client.get(f"/api/v1/tasks/{task['id']}/messages",headers=auth(owner_token)).status_code == 200
    sent = client.post(f"/api/v1/tasks/{task['id']}/messages",headers=auth(owner_token),json={"body":"Please bring gloves."})
    assert sent.status_code == 201, sent.text
    assert any(n["notification_type"] == "task_message" for n in client.get("/api/v1/me/notifications",headers=auth(attendee_token)).json())


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
    image_buffer = BytesIO()
    Image.new("RGB", (2, 2), (20, 40, 60)).save(image_buffer, format="PNG")
    image_bytes = image_buffer.getvalue()
    uploaded = client.post(f"/api/v1/tasks/{task_id}/proofs/before", headers=auth(worker_token),
                           files={"file": ("before.png", image_bytes, "image/png")})
    assert uploaded.status_code == 201, uploaded.text
    proof = uploaded.json()
    assert proof["proof_kind"] == "before"
    assert proof["content_type"] == "image/png"
    assert not (tmp_path / "public" / proof["original_name"]).exists()
    assert client.get(f"/api/v1/tasks/{task_id}/proofs", headers=auth(requester_token)).json()[0]["id"] == proof["id"]
    assert client.get(f"/api/v1/proofs/{proof['id']}/content", headers=auth(requester_token)).content.startswith(b"\x89PNG\r\n\x1a\n")
    assert client.get(f"/api/v1/proofs/{proof['id']}/content", headers=auth(outsider_token)).status_code == 403
    invalid = client.post(f"/api/v1/tasks/{task_id}/proofs/after", headers=auth(worker_token),
                          files={"file": ("fake.png", b"not an image", "image/png")})
    assert invalid.status_code == 415
    fake_png = b"\x89PNG\r\n\x1a\n" + b"not a decodable image"
    malformed = client.post(f"/api/v1/tasks/{task_id}/proofs/after", headers=auth(worker_token),
                            files={"file": ("fake.png", fake_png, "image/png")})
    assert malformed.status_code == 415
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


def test_login_rate_limit_returns_429():
    from app import main as main_module

    original_env = main_module.settings.app_env
    main_module.settings.app_env = "development"
    main_module._auth_attempts.clear()
    try:
        for _ in range(10):
            response = client.post("/api/v1/auth/login", json={
                "email": "not-present@example.com", "password": "wrong-password"
            })
            assert response.status_code == 401
        limited = client.post("/api/v1/auth/login", json={
            "email": "not-present@example.com", "password": "wrong-password"
        })
        assert limited.status_code == 429
        assert "retry-after" in limited.headers
    finally:
        main_module._auth_attempts.clear()
        main_module.settings.app_env = original_env
