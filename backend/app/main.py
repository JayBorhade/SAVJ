import json
import os
import hashlib
import secrets
import smtplib
import ssl
import logging
import re
from email.message import EmailMessage
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone
from io import BytesIO
import warnings
import threading
import time
from datetime import timedelta
from math import asin, cos, radians, sin, sqrt
from typing import Annotated
from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, Response, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from PIL import Image, UnidentifiedImageError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .config import get_settings
from .database import Base, engine, get_db
from .models import CommunityDrive, DriveParticipation, EmailActionToken, ImpactEvent, Message, Task, TaskProof, TaskRating, User, UserNotification
from .schemas import DriveCreate, DriveOut, EmailAddressRequest, EmailTokenRequest, MessageCreate, MessageOut, NotificationOut, PasswordResetConfirm, TaskCreate, TaskOut, TaskProofOut, TaskRatingCreate, TaskRatingOut, TokenOut, UserCreate, UserLogin, UserOut, UserUpdate, WorkerOut
from .security import create_access_token, decode_access_token_claims, hash_password, verify_password

settings = get_settings()
logger = logging.getLogger("savj.auth")
app = FastAPI(title="SAVJ API", version="0.1.0", description="Authenticated API for the SAVJ environmental community platform.")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True, allow_methods=["GET", "POST", "PATCH", "OPTIONS"], allow_headers=["Authorization", "Content-Type", "If-Match"])

@app.middleware("http")
async def security_headers(request, call_next):
    """Set conservative browser security headers on API responses."""
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    if settings.app_env.lower() in {"production", "prod"}:
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response
# Per-process defense-in-depth limiter. Production must also enforce shared limits at its gateway.
_AUTH_LIMITS = {"/api/v1/auth/login": (10, 60), "/api/v1/auth/register": (5, 60), "/api/v1/auth/verification-request": (3, 3600), "/api/v1/auth/password-reset/request": (3, 3600), "/api/v1/auth/password-reset/confirm": (10, 3600), "/api/v1/auth/verify-email": (10, 3600), "/api/v1/tasks": (10, 60), "/api/v1/drives": (5, 60)}
_ROUTE_LIMITS = [(re.compile(r"/api/v1/tasks/\d+/messages"), (30, 60)), (re.compile(r"/api/v1/tasks/\d+/rating"), (5, 3600)), (re.compile(r"/api/v1/tasks/\d+/proofs/(before|after)"), (10, 60)), (re.compile(r"/api/v1/drives/\d+/join"), (20, 60))]
_auth_attempts: dict[tuple[str, str], list[float]] = {}
_auth_attempts_lock = threading.Lock()

@app.middleware("http")
async def limit_rate_limited_requests(request: Request, call_next):
    if settings.app_env.lower() in {"test", "testing"}:
        return await call_next(request)
    policy = _AUTH_LIMITS.get(request.url.path)
    if policy is None:
        policy = next((limit for pattern, limit in _ROUTE_LIMITS if pattern.fullmatch(request.url.path)), None)
    if request.method == "POST" and policy:
        ip = request.client.host if request.client else "unknown"
        maximum, window = policy
        now = time.monotonic()
        key = (ip, request.url.path)
        with _auth_attempts_lock:
            recent = [stamp for stamp in _auth_attempts.get(key, []) if now - stamp < window]
            if len(recent) >= maximum:
                return JSONResponse(status_code=429, content={"detail": "Too many requests. Try again later."}, headers={"Retry-After": str(max(1, int(window - (now - recent[0]))))})
            recent.append(now)
            _auth_attempts[key] = recent
            if len(_auth_attempts) > 10000:
                cutoff = now - window
                for old_key, values in list(_auth_attempts.items()):
                    if not values or values[-1] <= cutoff:
                        _auth_attempts.pop(old_key, None)
                overflow = len(_auth_attempts) - 10000
                if overflow > 0:
                    oldest = sorted(_auth_attempts.items(), key=lambda item: item[1][-1] if item[1] else 0)
                    for old_key, _ in oldest[:overflow]:
                        _auth_attempts.pop(old_key, None)
    return await call_next(request)

_ACCESS_COOKIE = "savj_access"
_PRODUCTION = settings.app_env.lower() in {"production", "prod"}
_COOKIE_PATH = "/api/v1"
bearer = HTTPBearer(auto_error=False)


@app.middleware("http")
async def protect_cookie_authenticated_writes(request: Request, call_next):
    # SameSite=Lax is useful defense-in-depth; validate Origin as well because
    # browser cookies are ambient credentials and may otherwise enable CSRF.
    if (
        _PRODUCTION
        and request.method in {"POST", "PUT", "PATCH", "DELETE"}
        and request.cookies.get(_ACCESS_COOKIE)
        and not request.headers.get("authorization")
    ):
        origin = request.headers.get("origin")
        if not origin or origin.rstrip("/") not in settings.cors_origin_list:
            return JSONResponse(status_code=403, content={"detail": "Request origin is not allowed."})
    return await call_next(request)


def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    raw_token = credentials.credentials if credentials else request.cookies.get(_ACCESS_COOKIE)
    if not raw_token:
        raise HTTPException(status_code=401, detail="Authentication required.")
    user_id, token_version = decode_access_token_claims(raw_token)
    user = db.get(User, user_id)
    if not user or not user.is_active or user.token_version != token_version:
        raise HTTPException(status_code=401, detail="User session is unavailable or has been revoked.")
    return user


def _action_token_hash(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def _create_action_token(db: Session, user: User, purpose: str, lifetime: timedelta) -> str:
    # Serialize token issuance per user so an older link is invalidated when a
    # newer verification/reset request is issued.
    locked_user = db.scalar(select(User).where(User.id == user.id).with_for_update())
    if not locked_user:
        raise HTTPException(status_code=404, detail="User not found.")
    now = datetime.now(timezone.utc)
    active_tokens = db.scalars(
        select(EmailActionToken).where(
            EmailActionToken.user_id == user.id,
            EmailActionToken.purpose == purpose,
            EmailActionToken.used_at.is_(None),
        )
    ).all()
    for active_token in active_tokens:
        active_token.used_at = now
    raw_token = secrets.token_urlsafe(32)
    db.add(EmailActionToken(
        user_id=user.id,
        token_hash=_action_token_hash(raw_token),
        purpose=purpose,
        expires_at=now + lifetime,
    ))
    db.commit()
    return raw_token


def _send_action_email(recipient: str, purpose: str, raw_token: str) -> None:
    if not settings.smtp_host or not settings.smtp_from or not settings.public_app_url:
        raise RuntimeError("Email delivery is not configured.")
    if purpose == "verify_email":
        action = "verify-email"
        subject = "Verify your SAVJ email address"
        lead = "Verify your email address to activate your SAVJ account."
    elif purpose == "password_reset":
        action = "reset-password"
        subject = "Reset your SAVJ password"
        lead = "Use the secure link below to reset your SAVJ password."
    else:
        raise ValueError("Unsupported email action.")
    url = f"{settings.public_app_url.rstrip('/')}/?action={action}&token={raw_token}"
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.smtp_from
    message["To"] = recipient
    message.set_content(
        f"{lead}\n\n{url}\n\n"
        "If you did not request this, you can ignore this message. "
        "For your security, this link expires and can only be used once."
    )
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
        server.ehlo()
        if settings.smtp_starttls:
            server.starttls(context=ssl.create_default_context())
            server.ehlo()
        if settings.smtp_username:
            server.login(settings.smtp_username, settings.smtp_password or "")
        server.send_message(message)


def _valid_action_token(db: Session, raw_token: str, purpose: str) -> EmailActionToken | None:
    token = db.scalar(
        select(EmailActionToken)
        .where(
            EmailActionToken.token_hash == _action_token_hash(raw_token),
            EmailActionToken.purpose == purpose,
            EmailActionToken.used_at.is_(None),
        )
        .with_for_update()
    )
    if not token:
        return None
    expiry = token.expires_at
    if expiry.tzinfo is None or expiry.utcoffset() is None:
        expiry = expiry.replace(tzinfo=timezone.utc)
    if expiry <= datetime.now(timezone.utc):
        return None
    return token


def _send_action_email_safely(recipient: str, purpose: str, raw_token: str) -> None:
    try:
        _send_action_email(recipient, purpose, raw_token)
    except Exception as exc:
        # Do not log recipient addresses, raw tokens, action URLs, or SMTP
        # exception text, which may contain personal data. Users can retry.
        logger.error("SAVJ email delivery failed for action %s (%s)", purpose, type(exc).__name__)


def issue_auth_response(user: User, response: Response) -> TokenOut | JSONResponse:
    token, seconds = create_access_token(user.id, user.token_version)
    if _PRODUCTION:
        # Return the cookie-setting response itself so the Set-Cookie header is
        # preserved by every ASGI middleware and response-model path.
        payload = TokenOut(access_token=None, expires_in=seconds, user=user_output(user))
        cookie_response = JSONResponse(content=payload.model_dump(mode="json"))
        cookie_response.set_cookie(
            key=_ACCESS_COOKIE,
            value=token,
            max_age=seconds,
            httponly=True,
            secure=True,
            samesite="lax",
            path=_COOKIE_PATH,
        )
        return cookie_response
    return TokenOut(access_token=token, expires_in=seconds, user=user_output(user))

CurrentUser = Annotated[User, Depends(get_current_user)]
Database = Annotated[Session, Depends(get_db)]

def user_output(user: User) -> UserOut:
    return UserOut(id=user.id, email=user.email, display_name=user.display_name, locality=user.locality, purpose=user.purpose, skills=json.loads(user.skills_json), tools=json.loads(user.tools_json), created_at=user.created_at)

def task_access(db: Session, task_id: int, user_id: int) -> Task:
    task = db.get(Task, task_id)
    if not task: raise HTTPException(status_code=404, detail="Task not found.")
    if user_id not in {task.requester_id, task.worker_id}: raise HTTPException(status_code=403, detail="You are not a participant in this task.")
    return task

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "savj-api"}

@app.post("/api/v1/auth/register", response_model=TokenOut, status_code=201)
def register(payload: UserCreate, response: Response, db: Database) -> TokenOut:
    email = str(payload.email).lower()
    user = User(
        email=email,
        display_name=payload.display_name.strip(),
        password_hash=hash_password(payload.password),
        locality=payload.locality.strip(),
        purpose=payload.purpose,
        skills_json=json.dumps(sorted({s.strip() for s in payload.skills if s.strip()})),
        tools_json=json.dumps(sorted({t.strip() for t in payload.tools if t.strip()})),
        is_email_verified=not _PRODUCTION,
    )
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists.") from None
    if _PRODUCTION:
        raw_token = _create_action_token(db, user, "verify_email", timedelta(hours=24))
        _send_action_email_safely(user.email, "verify_email", raw_token)
        return TokenOut(access_token=None, expires_in=0, user=user_output(user), requires_email_verification=True)
    return issue_auth_response(user, response)

@app.post("/api/v1/auth/login", response_model=TokenOut)
def login(payload: UserLogin, response: Response, db: Database) -> TokenOut:
    user = db.scalar(select(User).where(User.email == str(payload.email).lower()))
    if not user or not verify_password(payload.password, user.password_hash) or not user.is_active:
        raise HTTPException(status_code=401, detail="Email or password is incorrect.")
    if _PRODUCTION and not user.is_email_verified:
        raise HTTPException(status_code=403, detail="Verify your email address before signing in.")
    return issue_auth_response(user, response)


@app.post("/api/v1/auth/verification-request", status_code=202)
def request_email_verification(payload: EmailAddressRequest, db: Database) -> dict[str, str]:
    user = db.scalar(select(User).where(User.email == str(payload.email).lower()))
    if user and user.is_active and not user.is_email_verified:
        raw_token = _create_action_token(db, user, "verify_email", timedelta(hours=24))
        _send_action_email_safely(user.email, "verify_email", raw_token)
    return {"message": "If this account needs verification, an email will be sent shortly."}


@app.post("/api/v1/auth/verify-email")
def verify_email(payload: EmailTokenRequest, db: Database) -> dict[str, str]:
    token = _valid_action_token(db, payload.token, "verify_email")
    if not token:
        raise HTTPException(status_code=400, detail="This verification link is invalid or expired.")
    user = db.get(User, token.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=400, detail="This verification link is invalid or expired.")
    token.used_at = datetime.now(timezone.utc)
    user.is_email_verified = True
    db.commit()
    return {"message": "Email verified. You can now sign in to SAVJ."}


@app.post("/api/v1/auth/password-reset/request", status_code=202)
def request_password_reset(payload: EmailAddressRequest, db: Database) -> dict[str, str]:
    user = db.scalar(select(User).where(User.email == str(payload.email).lower()))
    if user and user.is_active:
        raw_token = _create_action_token(db, user, "password_reset", timedelta(minutes=30))
        _send_action_email_safely(user.email, "password_reset", raw_token)
    return {"message": "If an active account exists, password-reset instructions will be sent shortly."}


@app.post("/api/v1/auth/password-reset/confirm")
def confirm_password_reset(payload: PasswordResetConfirm, response: Response, db: Database) -> dict[str, str]:
    token = _valid_action_token(db, payload.token, "password_reset")
    if not token:
        raise HTTPException(status_code=400, detail="This password-reset link is invalid or expired.")
    user = db.get(User, token.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=400, detail="This password-reset link is invalid or expired.")
    now = datetime.now(timezone.utc)
    token.used_at = now
    other_tokens = db.scalars(
        select(EmailActionToken).where(
            EmailActionToken.user_id == user.id,
            EmailActionToken.purpose == "password_reset",
            EmailActionToken.used_at.is_(None),
            EmailActionToken.id != token.id,
        )
    ).all()
    for other in other_tokens:
        other.used_at = now
    user.password_hash = hash_password(payload.new_password)
    user.token_version += 1
    db.commit()
    response.delete_cookie(key=_ACCESS_COOKIE, path=_COOKIE_PATH, httponly=True, secure=_PRODUCTION, samesite="lax")
    return {"message": "Password reset successfully. Sign in with your new password."}


@app.post("/api/v1/auth/logout", status_code=204)
def logout(user: CurrentUser, db: Database, response: Response) -> Response:
    # Incrementing token_version revokes every access token issued before logout.
    user.token_version += 1
    db.commit()
    response.delete_cookie(
        key=_ACCESS_COOKIE,
        path=_COOKIE_PATH,
        httponly=True,
        secure=_PRODUCTION,
        samesite="lax",
    )
    response.status_code = 204
    return response

@app.get("/api/v1/me", response_model=UserOut)
def get_me(user: CurrentUser) -> UserOut:
    return user_output(user)

@app.patch("/api/v1/me", response_model=UserOut)
def update_me(payload: UserUpdate, user: CurrentUser, db: Database) -> UserOut:
    for key, value in payload.model_dump(exclude_unset=True).items():
        if value is None: continue
        if key == "skills": user.skills_json = json.dumps(sorted({item.strip() for item in value if item.strip()}))
        elif key == "tools": user.tools_json = json.dumps(sorted({item.strip() for item in value if item.strip()}))
        else: setattr(user, key, value.strip() if isinstance(value, str) else value)
    db.commit()
    db.refresh(user)
    return user_output(user)

@app.post("/api/v1/tasks", response_model=TaskOut, status_code=201)
def create_task(payload: TaskCreate, user: CurrentUser, db: Database) -> Task:
    task = Task(requester_id=user.id, title=payload.title.strip(), description=payload.description.strip(), category=payload.category.strip(), required_skills_json=json.dumps(payload.required_skills), required_tools_json=json.dumps(payload.required_tools), location_text=payload.location_text.strip(), private_location_text=payload.private_location_text, latitude=payload.latitude, longitude=payload.longitude, budget_minor_units=payload.budget_rupees * 100, scheduled_at=payload.scheduled_at, status="Open")
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

def task_response_for_viewer(task: Task, viewer_id: int) -> TaskOut:
    payload = TaskOut.model_validate(task)
    # Keep precise household addresses and coordinates private while a task is
    # open. Browsers see the public locality and coarse map coordinates only.
    if task.status == "Open" and viewer_id != task.requester_id:
        payload.private_location_text = None
        if payload.latitude is not None:
            payload.latitude = round(payload.latitude, 2)
        if payload.longitude is not None:
            payload.longitude = round(payload.longitude, 2)
    return payload


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    value = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 6371.0088 * 2 * asin(sqrt(min(1.0, value)))

@app.get("/api/v1/tasks", response_model=list[TaskOut])
def list_tasks(db: Database, user: CurrentUser, status_filter: str | None = Query(default=None, alias="status"), category: str | None = None, search: str | None = None, latitude: float | None = Query(default=None, ge=-90, le=90), longitude: float | None = Query(default=None, ge=-180, le=180), radius_km: float | None = Query(default=None, gt=0, le=100), limit: int = Query(default=30, ge=1, le=100), offset: int = Query(default=0, ge=0)) -> list[TaskOut]:
    if (latitude is None) != (longitude is None):
        raise HTTPException(status_code=422, detail="Latitude and longitude must be supplied together.")
    if radius_km is not None and latitude is None:
        raise HTTPException(status_code=422, detail="A radius requires latitude and longitude.")
    # Open tasks are discoverable to authenticated users. Non-open tasks are
    # visible only to their requester and assigned worker, even when callers
    # manually request a private status through query parameters.
    query = select(Task).where(
        or_(Task.status == "Open", Task.requester_id == user.id, Task.worker_id == user.id)
    )
    if status_filter:
        if status_filter not in {"Open", "Accepted", "In progress", "Awaiting approval", "Completed", "Cancelled"}: raise HTTPException(status_code=422, detail="Unsupported task status.")
        query = query.where(Task.status == status_filter)
    if category: query = query.where(Task.category == category)
    if search: query = query.where(Task.title.ilike("%" + search[:100] + "%"))
    if latitude is not None and longitude is not None and radius_km is not None:
        lat_delta = radius_km / 110.574
        lon_delta = min(180.0, radius_km / max(0.1, 111.320 * cos(radians(latitude))))
        query = query.where(Task.latitude.is_not(None), Task.longitude.is_not(None),
                            Task.latitude.between(max(-90, latitude-lat_delta), min(90, latitude+lat_delta)),
                            Task.longitude.between(max(-180, longitude-lon_delta), min(180, longitude+lon_delta)))
        candidates = list(db.scalars(query.order_by(Task.created_at.desc())).all())
        nearby = [task for task in candidates if _distance_km(latitude, longitude, task.latitude, task.longitude) <= radius_km]
        return [task_response_for_viewer(task, user.id) for task in nearby[offset:offset+limit]]
    tasks = list(db.scalars(query.order_by(Task.created_at.desc()).offset(offset).limit(limit)).all())
    return [task_response_for_viewer(task, user.id) for task in tasks]

@app.get("/api/v1/tasks/{task_id}", response_model=TaskOut)
def get_task(task_id: int, user: CurrentUser, db: Database) -> TaskOut:
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    # Open tasks are discoverable to signed-in users. Once accepted, task details
    # are private to the requester and assigned worker to avoid leaking location,
    # schedule, budget, or participant identifiers to unrelated accounts.
    if task.status != "Open" and user.id not in {task.requester_id, task.worker_id}:
        raise HTTPException(status_code=404, detail="Task not found.")
    return task_response_for_viewer(task, user.id)

@app.get("/api/v1/tasks/{task_id}/rating", response_model=TaskRatingOut | None)
def get_task_rating(task_id: int, user: CurrentUser, db: Database) -> TaskRating | None:
    task = db.get(Task, task_id)
    if not task or user.id not in {task.requester_id, task.worker_id}:
        raise HTTPException(status_code=404, detail="Task rating not found.")
    return db.scalar(select(TaskRating).where(TaskRating.task_id == task_id))


@app.post("/api/v1/tasks/{task_id}/rating", response_model=TaskRatingOut, status_code=201)
def create_task_rating(task_id: int, payload: TaskRatingCreate, user: CurrentUser, db: Database) -> TaskRating:
    task = db.scalar(select(Task).where(Task.id == task_id).with_for_update())
    if not task or user.id != task.requester_id:
        raise HTTPException(status_code=404, detail="Completed task not found.")
    if task.status != "Completed" or task.worker_id is None:
        raise HTTPException(status_code=409, detail="Only a completed task with an assigned worker can be rated.")
    existing = db.scalar(select(TaskRating).where(TaskRating.task_id == task.id))
    if existing:
        raise HTTPException(status_code=409, detail="This task has already been rated.")
    rating = TaskRating(
        task_id=task.id,
        requester_id=user.id,
        worker_id=task.worker_id,
        score=payload.score,
        comment=payload.comment,
    )
    db.add(rating)
    try:
        db.commit()
        db.refresh(rating)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="This task has already been rated.") from None
    return rating


def transition(db: Session, task: Task, target: str, actor: User) -> Task:
    # Always re-read and lock the latest row before validating a transition.
    # This serializes status changes and prevents duplicate completion events
    # when two requests race (PostgreSQL production path).
    locked_task = db.scalar(select(Task).where(Task.id == task.id).with_for_update())
    if not locked_task:
        raise HTTPException(status_code=404, detail="Task not found.")
    task = locked_task
    allowed = {"Open":{"Accepted","Cancelled"},"Accepted":{"In progress","Cancelled"},"In progress":{"Awaiting approval","Cancelled"},"Awaiting approval":{"Completed","In progress"},"Completed":set(),"Cancelled":set()}
    if target not in allowed.get(task.status, set()): raise HTTPException(status_code=409, detail=f"Cannot transition task from {task.status} to {target}.")
    if target == "Accepted":
        if actor.id == task.requester_id: raise HTTPException(status_code=403, detail="Requesters cannot accept their own task.")
        if actor.purpose == "Requester": raise HTTPException(status_code=403, detail="Your account is not enabled for worker tasks.")
        if task.worker_id is not None: raise HTTPException(status_code=409, detail="This task has already been accepted.")
        worker_skills = {item.casefold() for item in json.loads(actor.skills_json)}
        worker_tools = {item.casefold() for item in json.loads(actor.tools_json)}
        missing_skills = [item for item in task.required_skills if item.casefold() not in worker_skills]
        missing_tools = [item for item in task.required_tools if item.casefold() not in worker_tools]
        if missing_skills or missing_tools:
            missing = []
            if missing_skills: missing.append("skills: " + ", ".join(missing_skills))
            if missing_tools: missing.append("tools: " + ", ".join(missing_tools))
            raise HTTPException(status_code=409, detail="Your profile does not meet this task's mandatory requirements (" + "; ".join(missing) + ").")
        task.worker_id = actor.id
    elif target == "In progress":
        if task.status == "Awaiting approval":
            if actor.id != task.requester_id:
                raise HTTPException(status_code=403, detail="Only the requester can request rework.")
        elif actor.id != task.worker_id:
            raise HTTPException(status_code=403, detail="Only the assigned worker can start this task.")
    elif target == "Awaiting approval":
        if actor.id != task.worker_id:
            raise HTTPException(status_code=403, detail="Only the assigned worker can submit this task for approval.")
        # Each work attempt must have fresh before and after evidence uploaded
        # by the assigned worker after the task was started or sent back for rework.
        proof_kinds = set(db.scalars(
            select(TaskProof.proof_kind).where(
                TaskProof.task_id == task.id,
                TaskProof.uploader_id == actor.id,
                TaskProof.created_at >= task.updated_at,
            )
        ).all())
        if not {"before", "after"}.issubset(proof_kinds):
            raise HTTPException(status_code=409, detail="Upload fresh before and after proof images before submitting for approval.")
    elif target == "Completed":
        if actor.id != task.requester_id: raise HTTPException(status_code=403, detail="Only the requester can approve completion.")
        db.add(ImpactEvent(user_id=task.worker_id or actor.id, task_id=task.id, event_type="task_completed", verified_at=datetime.now(timezone.utc)))
    elif target == "Cancelled":
        if actor.id not in {task.requester_id, task.worker_id}: raise HTTPException(status_code=403, detail="Only task participants can cancel this task.")
    recipient_id: int | None = None
    notification_type = "task_status"
    notification_title = "Task updated"
    notification_body = f"{task.title}: {target.lower()}."
    if target == "Accepted":
        recipient_id, notification_type, notification_title = task.requester_id, "task_accepted", "Your task was accepted"
        notification_body = f"{task.title} has been accepted by a worker."
    elif target == "In progress" and task.status == "Accepted":
        recipient_id, notification_type, notification_title = task.requester_id, "task_started", "Work has started"
        notification_body = f"A worker has started: {task.title}."
    elif target == "In progress" and task.status == "Awaiting approval":
        recipient_id, notification_type, notification_title = task.worker_id, "task_rework", "Rework requested"
        notification_body = f"The requester asked for changes to: {task.title}."
    elif target == "Awaiting approval":
        recipient_id, notification_type, notification_title = task.requester_id, "task_submitted", "Work is ready for review"
        notification_body = f"The worker submitted {task.title} for your approval."
    elif target == "Completed":
        recipient_id, notification_type, notification_title = task.worker_id, "task_completed", "Task completion approved"
        notification_body = f"The requester approved your work on {task.title}."
    elif target == "Cancelled":
        recipient_id = task.worker_id if actor.id == task.requester_id else task.requester_id
        notification_type, notification_title = "task_cancelled", "Task cancelled"
        notification_body = f"{task.title} was cancelled."
    if recipient_id and recipient_id != actor.id:
        db.add(UserNotification(
            user_id=recipient_id,
            notification_type=notification_type,
            title=notification_title,
            body=notification_body,
            task_id=task.id,
        ))
    task.status = target
    task.version += 1
    task.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(task)
    return task

@app.post("/api/v1/tasks/{task_id}/accept", response_model=TaskOut)
def accept_task(task_id: int, user: CurrentUser, db: Database) -> Task:
    # Lock the task row while checking/assigning its worker to prevent two
    # concurrent accept requests from both winning on PostgreSQL.
    task = db.scalar(
        select(Task).where(Task.id == task_id).with_for_update()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    return transition(db, task, "Accepted", user)

@app.post("/api/v1/tasks/{task_id}/start", response_model=TaskOut)
def start_task(task_id: int, user: CurrentUser, db: Database) -> Task:
    return transition(db, task_access(db, task_id, user.id), "In progress", user)

@app.post("/api/v1/tasks/{task_id}/submit", response_model=TaskOut)
def submit_task(task_id: int, user: CurrentUser, db: Database) -> Task:
    return transition(db, task_access(db, task_id, user.id), "Awaiting approval", user)

@app.post("/api/v1/tasks/{task_id}/approve", response_model=TaskOut)
def approve_task(task_id: int, user: CurrentUser, db: Database) -> Task:
    return transition(db, task_access(db, task_id, user.id), "Completed", user)

@app.post("/api/v1/tasks/{task_id}/cancel", response_model=TaskOut)
def cancel_task(task_id: int, user: CurrentUser, db: Database) -> Task:
    return transition(db, task_access(db, task_id, user.id), "Cancelled", user)

def drive_output(drive: CommunityDrive, count: int) -> DriveOut:
    return DriveOut(id=drive.id, organizer_id=drive.organizer_id, title=drive.title, description=drive.description, location_text=drive.location_text, starts_at=drive.starts_at, capacity=drive.capacity, status=drive.status, participant_count=count)

@app.post("/api/v1/drives", response_model=DriveOut, status_code=201)
def create_drive(payload: DriveCreate, user: CurrentUser, db: Database) -> DriveOut:
    drive = CommunityDrive(organizer_id=user.id, title=payload.title.strip(), description=payload.description.strip(), location_text=payload.location_text.strip(), starts_at=payload.starts_at, capacity=payload.capacity)
    db.add(drive)
    db.commit()
    db.refresh(drive)
    return drive_output(drive, 0)

@app.get("/api/v1/drives", response_model=list[DriveOut])
def list_drives(db: Database, user: CurrentUser, limit: int = Query(default=30, ge=1, le=100), offset: int = Query(default=0, ge=0)) -> list[DriveOut]:
    drives = db.scalars(select(CommunityDrive).where(CommunityDrive.status == "Open").order_by(CommunityDrive.starts_at).offset(offset).limit(limit)).all()
    return [drive_output(d, db.scalar(select(func.count(DriveParticipation.id)).where(DriveParticipation.drive_id == d.id)) or 0) for d in drives]

@app.post("/api/v1/drives/{drive_id}/join", status_code=201)
def join_drive(drive_id: int, user: CurrentUser, db: Database) -> dict[str, str]:
    # Serialize capacity checks on PostgreSQL so concurrent joins cannot
    # overbook the same drive. SQLite ignores FOR UPDATE; production uses Postgres.
    drive = db.scalar(
        select(CommunityDrive)
        .where(CommunityDrive.id == drive_id)
        .with_for_update()
    )
    if not drive or drive.status != "Open": raise HTTPException(status_code=404, detail="Open community drive not found.")
    existing = db.scalar(select(DriveParticipation).where(DriveParticipation.drive_id == drive_id, DriveParticipation.user_id == user.id))
    if existing: return {"status":"already_joined"}
    count = db.scalar(select(func.count(DriveParticipation.id)).where(DriveParticipation.drive_id == drive_id)) or 0
    if drive.capacity is not None and count >= drive.capacity: raise HTTPException(status_code=409, detail="This drive is full.")
    db.add(DriveParticipation(drive_id=drive_id, user_id=user.id))
    if drive.organizer_id != user.id:
        db.add(UserNotification(
            user_id=drive.organizer_id,
            notification_type="drive_joined",
            title="Someone joined your drive",
            body=f"{user.display_name} joined {drive.title}.",
            drive_id=drive.id,
        ))
    try: db.commit()
    except IntegrityError:
        db.rollback()
        return {"status":"already_joined"}
    return {"status":"joined"}


@app.get("/api/v1/workers", response_model=list[WorkerOut])
def list_workers(db: Database, user: CurrentUser, search: str | None = None, skill: str | None = None, limit: int = Query(default=50, ge=1, le=100), offset: int = Query(default=0, ge=0)) -> list[WorkerOut]:
    query = select(User).where(User.is_active.is_(True), User.purpose.in_(["Worker", "Both"]))
    if search:
        term = "%" + search.strip()[:100] + "%"
        query = query.where((User.display_name.ilike(term)) | (User.locality.ilike(term)))
    people = list(db.scalars(query.order_by(User.created_at.desc()).offset(offset).limit(limit)).all())
    rating_rows = db.execute(
        select(TaskRating.worker_id, func.avg(TaskRating.score), func.count(TaskRating.id))
        .group_by(TaskRating.worker_id)
    ).all()
    ratings = {worker_id: (float(average), int(count)) for worker_id, average, count in rating_rows}
    results = []
    for person in people:
        skills = json.loads(person.skills_json)
        if skill and not any(skill.casefold() in item.casefold() for item in skills):
            continue
        average, count = ratings.get(person.id, (0.0, 0))
        results.append(WorkerOut(id=person.id, display_name=person.display_name, locality=person.locality, purpose=person.purpose, skills=skills, tools=json.loads(person.tools_json), rating_average=round(average, 2) if count else None, rating_count=count, created_at=person.created_at))
    return results

@app.get("/api/v1/me/notifications", response_model=list[NotificationOut])
def list_notifications(user: CurrentUser, db: Database, limit: int = Query(default=50, ge=1, le=100)) -> list[UserNotification]:
    return list(db.scalars(
        select(UserNotification)
        .where(UserNotification.user_id == user.id)
        .order_by(UserNotification.created_at.desc(), UserNotification.id.desc())
        .limit(limit)
    ).all())


@app.post("/api/v1/me/notifications/{notification_id}/read", response_model=NotificationOut)
def mark_notification_read(notification_id: int, user: CurrentUser, db: Database) -> UserNotification:
    notification = db.scalar(
        select(UserNotification)
        .where(UserNotification.id == notification_id, UserNotification.user_id == user.id)
        .with_for_update()
    )
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found.")
    if notification.read_at is None:
        notification.read_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(notification)
    return notification


@app.post("/api/v1/me/notifications/read-all")
def mark_all_notifications_read(user: CurrentUser, db: Database) -> dict[str, int]:
    result = db.execute(
        update(UserNotification)
        .where(UserNotification.user_id == user.id, UserNotification.read_at.is_(None))
        .values(read_at=datetime.now(timezone.utc))
    )
    db.commit()
    return {"updated": int(result.rowcount or 0)}


@app.get("/api/v1/me/impact")
def my_impact(user: CurrentUser, db: Database) -> dict[str, int]:
    completed = db.scalar(select(func.count(ImpactEvent.id)).where(ImpactEvent.user_id == user.id, ImpactEvent.event_type == "task_completed", ImpactEvent.verified_at.is_not(None))) or 0
    drives = db.scalar(select(func.count(DriveParticipation.id)).where(DriveParticipation.user_id == user.id)) or 0
    return {"verified_completed_tasks":completed,"community_drives_joined":drives}

@app.get("/api/v1/tasks/{task_id}/messages", response_model=list[MessageOut])
def list_messages(task_id: int, user: CurrentUser, db: Database, limit: int = Query(default=50, ge=1, le=100)) -> list[Message]:
    task_access(db, task_id, user.id)
    return list(db.scalars(select(Message).where(Message.task_id == task_id).order_by(Message.created_at).limit(limit)).all())

@app.post("/api/v1/tasks/{task_id}/messages", response_model=MessageOut, status_code=201)
def send_message(task_id: int, payload: MessageCreate, user: CurrentUser, db: Database) -> Message:
    task = task_access(db, task_id, user.id)
    message = Message(task_id=task_id, sender_id=user.id, body=payload.body.strip())
    recipient_id = task.worker_id if user.id == task.requester_id else task.requester_id
    if recipient_id and recipient_id != user.id:
        db.add(UserNotification(
            user_id=recipient_id,
            notification_type="task_message",
            title="New task message",
            body=f"New message on {task.title}.",
            task_id=task.id,
        ))
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


# Files are stored outside the static frontend tree and are only served through
# authenticated, task-participant-authorized endpoints.
UPLOAD_DIR = Path(os.environ.get("SAVJ_UPLOAD_DIR", "private_uploads")).resolve()
MAX_PROOF_BYTES = 8 * 1024 * 1024
_ALLOWED_PROOF_TYPES = {
    "jpeg": ("image/jpeg", b"\xff\xd8\xff"),
    "png": ("image/png", b"\x89PNG\r\n\x1a\n"),
    "webp": ("image/webp", b"RIFF"),
}

def _inspect_image(data: bytes) -> tuple[str, str, bytes]:
    if data.startswith(b"\xff\xd8\xff"):
        expected, content_type, extension = "JPEG", "image/jpeg", ".jpg"
    elif data.startswith(b"\x89PNG\r\n\x1a\n"):
        expected, content_type, extension = "PNG", "image/png", ".png"
    elif len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        expected, content_type, extension = "WEBP", "image/webp", ".webp"
    else:
        raise HTTPException(status_code=415, detail="Upload a valid JPEG, PNG, or WebP image.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as image:
                if image.format != expected or getattr(image, "n_frames", 1) != 1:
                    raise HTTPException(status_code=415, detail="Unsupported or mismatched image content.")
                width, height = image.size
                if width < 1 or height < 1 or width * height > 40_000_000:
                    raise HTTPException(status_code=413, detail="Image dimensions exceed the supported limit.")
                image.load()
                clean = image.convert("RGB") if expected == "JPEG" else image.copy()
                output = BytesIO()
                options = {"format": expected}
                if expected == "JPEG":
                    options.update({"quality": 90, "optimize": True})
                elif expected == "PNG":
                    options.update({"optimize": True})
                else:
                    options.update({"quality": 90, "method": 4})
                clean.save(output, **options)
                clean.close()
                return content_type, extension, output.getvalue()
    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise HTTPException(status_code=415, detail="The uploaded file is not a valid supported image.") from None

@app.post("/api/v1/tasks/{task_id}/proofs/{proof_kind}", response_model=TaskProofOut, status_code=201)
async def upload_task_proof(
    task_id: int,
    proof_kind: str,
    user: CurrentUser,
    db: Database,
    file: UploadFile = File(...),
) -> TaskProof:
    if proof_kind not in {"before", "after"}:
        raise HTTPException(status_code=422, detail="Proof type must be 'before' or 'after'.")
    task = task_access(db, task_id, user.id)
    if task.worker_id != user.id:
        raise HTTPException(status_code=403, detail="Only the assigned worker can upload proof.")
    if task.status != "In progress":
        raise HTTPException(status_code=409, detail="Proof can only be uploaded while the task is in progress.")
    data = await file.read(MAX_PROOF_BYTES + 1)
    await file.close()
    if not data:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if len(data) > MAX_PROOF_BYTES:
        raise HTTPException(status_code=413, detail="Proof images must be 8 MB or smaller.")
    content_type, extension, data = _inspect_image(data)
    if len(data) > MAX_PROOF_BYTES:
        raise HTTPException(status_code=413, detail="Sanitized proof images must be 8 MB or smaller.")
    safe_original_name = Path(file.filename or "proof-image").name.replace("\x00", "")[:255] or "proof-image"
    storage_name = f"{uuid4().hex}{extension}"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    destination = (UPLOAD_DIR / storage_name).resolve()
    if destination.parent != UPLOAD_DIR:
        raise HTTPException(status_code=400, detail="Invalid upload path.")
    file_descriptor: int | None = None
    try:
        # Tighten an existing mounted directory too; mkdir(mode=...) does not
        # change permissions when the directory already exists.
        os.chmod(UPLOAD_DIR, 0o700)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        file_descriptor = os.open(destination, flags, 0o600)
        with os.fdopen(file_descriptor, "wb") as stored_file:
            file_descriptor = None
            stored_file.write(data)
    except OSError:
        if file_descriptor is not None:
            os.close(file_descriptor)
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail="Private proof storage permissions could not be secured.") from None
    proof = TaskProof(task_id=task.id, uploader_id=user.id, proof_kind=proof_kind,
                      original_name=safe_original_name, storage_name=storage_name,
                      content_type=content_type, size_bytes=len(data))
    db.add(proof)
    try:
        db.commit()
        db.refresh(proof)
    except Exception:
        db.rollback()
        destination.unlink(missing_ok=True)
        raise
    return proof

@app.get("/api/v1/tasks/{task_id}/proofs", response_model=list[TaskProofOut])
def list_task_proofs(task_id: int, user: CurrentUser, db: Database) -> list[TaskProof]:
    task_access(db, task_id, user.id)
    return list(db.scalars(select(TaskProof).where(TaskProof.task_id == task_id).order_by(TaskProof.created_at)).all())

@app.get("/api/v1/proofs/{proof_id}/content")
def download_task_proof(proof_id: int, user: CurrentUser, db: Database) -> FileResponse:
    proof = db.get(TaskProof, proof_id)
    if not proof:
        raise HTTPException(status_code=404, detail="Proof image not found.")
    task_access(db, proof.task_id, user.id)
    path = (UPLOAD_DIR / proof.storage_name).resolve()
    if path.parent != UPLOAD_DIR or not path.is_file():
        raise HTTPException(status_code=404, detail="Proof image is unavailable.")
    return FileResponse(path, media_type=proof.content_type, filename=proof.original_name, content_disposition_type="inline")
