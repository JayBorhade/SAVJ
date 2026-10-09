import json
from datetime import datetime, timezone
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .config import get_settings
from .database import Base, engine, get_db
from .models import CommunityDrive, DriveParticipation, ImpactEvent, Message, Task, User
from .schemas import DriveCreate, DriveOut, MessageCreate, MessageOut, TaskCreate, TaskOut, TokenOut, UserCreate, UserLogin, UserOut, UserUpdate
from .security import create_access_token, decode_access_token, hash_password, verify_password

settings = get_settings()
Base.metadata.create_all(bind=engine)
app = FastAPI(title="SAVJ API", version="0.1.0", description="Authenticated API for the SAVJ environmental community platform.")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True, allow_methods=["GET", "POST", "PATCH", "OPTIONS"], allow_headers=["Authorization", "Content-Type", "If-Match"])
bearer = HTTPBearer(auto_error=False)

def get_current_user(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)], db: Annotated[Session, Depends(get_db)]) -> User:
    if not credentials: raise HTTPException(status_code=401, detail="Authentication required.")
    user_id = decode_access_token(credentials.credentials)
    user = db.get(User, user_id)
    if not user or not user.is_active: raise HTTPException(status_code=401, detail="User is unavailable.")
    return user

CurrentUser = Annotated[User, Depends(get_current_user)]
Database = Annotated[Session, Depends(get_db)]

def user_output(user: User) -> UserOut:
    return UserOut(id=user.id, email=user.email, display_name=user.display_name, locality=user.locality, purpose=user.purpose, skills=json.loads(user.skills_json), created_at=user.created_at)

def task_access(db: Session, task_id: int, user_id: int) -> Task:
    task = db.get(Task, task_id)
    if not task: raise HTTPException(status_code=404, detail="Task not found.")
    if user_id not in {task.requester_id, task.worker_id}: raise HTTPException(status_code=403, detail="You are not a participant in this task.")
    return task

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "savj-api"}

@app.post("/api/v1/auth/register", response_model=TokenOut, status_code=201)
def register(payload: UserCreate, db: Database) -> TokenOut:
    email = str(payload.email).lower()
    user = User(email=email, display_name=payload.display_name.strip(), password_hash=hash_password(payload.password), locality=payload.locality.strip(), purpose=payload.purpose, skills_json=json.dumps(sorted({s.strip() for s in payload.skills if s.strip()})))
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists.") from None
    token, seconds = create_access_token(user.id)
    return TokenOut(access_token=token, expires_in=seconds, user=user_output(user))

@app.post("/api/v1/auth/login", response_model=TokenOut)
def login(payload: UserLogin, db: Database) -> TokenOut:
    user = db.scalar(select(User).where(User.email == str(payload.email).lower()))
    if not user or not verify_password(payload.password, user.password_hash) or not user.is_active:
        raise HTTPException(status_code=401, detail="Email or password is incorrect.")
    token, seconds = create_access_token(user.id)
    return TokenOut(access_token=token, expires_in=seconds, user=user_output(user))

@app.get("/api/v1/me", response_model=UserOut)
def get_me(user: CurrentUser) -> UserOut:
    return user_output(user)

@app.patch("/api/v1/me", response_model=UserOut)
def update_me(payload: UserUpdate, user: CurrentUser, db: Database) -> UserOut:
    for key, value in payload.model_dump(exclude_unset=True).items():
        if value is None: continue
        if key == "skills": user.skills_json = json.dumps(sorted({item.strip() for item in value if item.strip()}))
        else: setattr(user, key, value.strip() if isinstance(value, str) else value)
    db.commit()
    db.refresh(user)
    return user_output(user)

@app.post("/api/v1/tasks", response_model=TaskOut, status_code=201)
def create_task(payload: TaskCreate, user: CurrentUser, db: Database) -> Task:
    task = Task(requester_id=user.id, title=payload.title.strip(), description=payload.description.strip(), category=payload.category.strip(), location_text=payload.location_text.strip(), budget_minor_units=payload.budget_rupees * 100, scheduled_at=payload.scheduled_at, status="Open")
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@app.get("/api/v1/tasks", response_model=list[TaskOut])
def list_tasks(db: Database, user: CurrentUser, status_filter: str | None = Query(default=None, alias="status"), category: str | None = None, search: str | None = None, limit: int = Query(default=30, ge=1, le=100), offset: int = Query(default=0, ge=0)) -> list[Task]:
    query = select(Task)
    if status_filter:
        if status_filter not in {"Open", "Accepted", "In progress", "Awaiting approval", "Completed", "Cancelled"}: raise HTTPException(status_code=422, detail="Unsupported task status.")
        query = query.where(Task.status == status_filter)
    if category: query = query.where(Task.category == category)
    if search: query = query.where(Task.title.ilike("%" + search[:100] + "%"))
    return list(db.scalars(query.order_by(Task.created_at.desc()).offset(offset).limit(limit)).all())

@app.get("/api/v1/tasks/{task_id}", response_model=TaskOut)
def get_task(task_id: int, user: CurrentUser, db: Database) -> Task:
    task = db.get(Task, task_id)
    if not task: raise HTTPException(status_code=404, detail="Task not found.")
    return task

def transition(db: Session, task: Task, target: str, actor: User) -> Task:
    allowed = {"Open":{"Accepted","Cancelled"},"Accepted":{"In progress","Cancelled"},"In progress":{"Awaiting approval","Cancelled"},"Awaiting approval":{"Completed","In progress"},"Completed":set(),"Cancelled":set()}
    if target not in allowed.get(task.status, set()): raise HTTPException(status_code=409, detail=f"Cannot transition task from {task.status} to {target}.")
    if target == "Accepted":
        if actor.id == task.requester_id: raise HTTPException(status_code=403, detail="Requesters cannot accept their own task.")
        if actor.purpose == "Requester": raise HTTPException(status_code=403, detail="Your account is not enabled for worker tasks.")
        if task.worker_id is not None: raise HTTPException(status_code=409, detail="This task has already been accepted.")
        task.worker_id = actor.id
    elif target in {"In progress", "Awaiting approval"}:
        if actor.id != task.worker_id: raise HTTPException(status_code=403, detail="Only the assigned worker can update this task.")
    elif target == "Completed":
        if actor.id != task.requester_id: raise HTTPException(status_code=403, detail="Only the requester can approve completion.")
        db.add(ImpactEvent(user_id=task.worker_id or actor.id, task_id=task.id, event_type="task_completed", verified_at=datetime.now(timezone.utc)))
    elif target == "Cancelled":
        if actor.id not in {task.requester_id, task.worker_id}: raise HTTPException(status_code=403, detail="Only task participants can cancel this task.")
    elif task.status == "Awaiting approval" and target == "In progress":
        if actor.id != task.requester_id: raise HTTPException(status_code=403, detail="Only the requester can request rework.")
    task.status = target
    task.version += 1
    task.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(task)
    return task

@app.post("/api/v1/tasks/{task_id}/accept", response_model=TaskOut)
def accept_task(task_id: int, user: CurrentUser, db: Database) -> Task:
    task = db.get(Task, task_id)
    if not task: raise HTTPException(status_code=404, detail="Task not found.")
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
    drive = db.get(CommunityDrive, drive_id)
    if not drive or drive.status != "Open": raise HTTPException(status_code=404, detail="Open community drive not found.")
    existing = db.scalar(select(DriveParticipation).where(DriveParticipation.drive_id == drive_id, DriveParticipation.user_id == user.id))
    if existing: return {"status":"already_joined"}
    count = db.scalar(select(func.count(DriveParticipation.id)).where(DriveParticipation.drive_id == drive_id)) or 0
    if drive.capacity is not None and count >= drive.capacity: raise HTTPException(status_code=409, detail="This drive is full.")
    db.add(DriveParticipation(drive_id=drive_id, user_id=user.id))
    try: db.commit()
    except IntegrityError:
        db.rollback()
        return {"status":"already_joined"}
    return {"status":"joined"}

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
    task_access(db, task_id, user.id)
    message = Message(task_id=task_id, sender_id=user.id, body=payload.body.strip())
    db.add(message)
    db.commit()
    db.refresh(message)
    return message
