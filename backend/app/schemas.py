from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    display_name: str = Field(min_length=1, max_length=80)
    locality: str = Field(default="Pune, Maharashtra", min_length=1, max_length=160)
    purpose: str = Field(default="Both", pattern="^(Requester|Worker|Both)$")
    skills: list[str] = Field(default_factory=list, max_length=30)
    tools: list[str] = Field(default_factory=list, max_length=30)
    @field_validator("tools")
    @classmethod
    def normalize_tools(cls, value: list[str]) -> list[str]:
        cleaned = []
        for item in value:
            tool = item.strip()
            if not tool:
                continue
            if len(tool) > 80:
                raise ValueError("Each tool must be 80 characters or fewer.")
            cleaned.append(tool)
        return list(dict.fromkeys(cleaned))

    @field_validator("skills")
    @classmethod
    def normalize_skills(cls, value: list[str]) -> list[str]:
        cleaned = []
        for item in value:
            skill = item.strip()
            if not skill:
                continue
            if len(skill) > 80:
                raise ValueError("Each skill must be 80 characters or fewer.")
            cleaned.append(skill)
        return list(dict.fromkeys(cleaned))

    @field_validator("display_name", "locality")
    @classmethod
    def trim_required(cls, value: str) -> str:
        value = value.strip()
        if not value: raise ValueError("This field cannot be blank.")
        return value

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

class UserUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=80)
    locality: str | None = Field(default=None, min_length=1, max_length=160)
    purpose: str | None = Field(default=None, pattern="^(Requester|Worker|Both)$")
    skills: list[str] | None = Field(default=None, max_length=30)
    tools: list[str] | None = Field(default=None, max_length=30)

    @field_validator("tools")
    @classmethod
    def normalize_updated_tools(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        cleaned = []
        for item in value:
            tool = item.strip()
            if not tool:
                continue
            if len(tool) > 80:
                raise ValueError("Each tool must be 80 characters or fewer.")
            cleaned.append(tool)
        return list(dict.fromkeys(cleaned))

    @field_validator("display_name", "locality")
    @classmethod
    def trim_nonempty_profile_fields(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank.")
        return value

    @field_validator("skills")
    @classmethod
    def normalize_updated_skills(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        cleaned = []
        for item in value:
            skill = item.strip()
            if not skill:
                continue
            if len(skill) > 80:
                raise ValueError("Each skill must be 80 characters or fewer.")
            cleaned.append(skill)
        return list(dict.fromkeys(cleaned))

class UserOut(BaseModel):
    id: int
    email: EmailStr
    display_name: str
    locality: str
    purpose: str
    skills: list[str]
    tools: list[str] = Field(default_factory=list)
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class TokenOut(BaseModel):
    access_token: str | None = None
    token_type: str = "bearer"
    expires_in: int
    user: UserOut
    requires_email_verification: bool = False

class EmailAddressRequest(BaseModel):
    email: EmailStr

class EmailTokenRequest(BaseModel):
    token: str = Field(min_length=32, max_length=128)

class PasswordResetConfirm(BaseModel):
    token: str = Field(min_length=32, max_length=128)
    new_password: str = Field(min_length=10, max_length=128)

class TaskCreate(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    description: str = Field(default="", max_length=4000)
    category: str = Field(default="Community cleanup", min_length=1, max_length=80)
    required_skills: list[str] = Field(default_factory=list, max_length=20)
    required_tools: list[str] = Field(default_factory=list, max_length=20)
    location_text: str = Field(min_length=2, max_length=200)
    budget_rupees: int = Field(ge=0, le=10000000)
    scheduled_at: datetime | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    @field_validator("required_skills", "required_tools")
    @classmethod
    def normalize_requirements(cls, value: list[str]) -> list[str]:
        cleaned = []
        for item in value:
            requirement = item.strip()
            if not requirement:
                continue
            if len(requirement) > 80:
                raise ValueError("Each requirement must be 80 characters or fewer.")
            cleaned.append(requirement)
        return list(dict.fromkeys(cleaned))

    @field_validator("scheduled_at")
    @classmethod
    def validate_scheduled_at(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Scheduled time must include a timezone.")
        if value <= datetime.now(timezone.utc):
            raise ValueError("Scheduled time must be in the future.")
        return value

    @field_validator("title", "location_text", "category")
    @classmethod
    def trim_task_fields(cls, value: str) -> str:
        value = value.strip()
        if not value: raise ValueError("This field cannot be blank.")
        return value

class TaskOut(BaseModel):
    id: int
    requester_id: int
    worker_id: int | None
    title: str
    description: str
    category: str
    location_text: str
    latitude: float | None = None
    longitude: float | None = None
    budget_minor_units: int
    currency: str
    status: str
    scheduled_at: datetime | None
    version: int
    created_at: datetime
    updated_at: datetime
    required_skills: list[str] = Field(default_factory=list)
    required_tools: list[str] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)

class DriveCreate(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    description: str = Field(default="", max_length=4000)
    location_text: str = Field(min_length=2, max_length=200)
    starts_at: datetime
    capacity: int | None = Field(default=None, ge=1, le=100000)

    @field_validator("title", "location_text")
    @classmethod
    def trim_required_drive_fields(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank.")
        return value

    @field_validator("description")
    @classmethod
    def trim_drive_description(cls, value: str) -> str:
        return value.strip()

    @field_validator("starts_at")
    @classmethod
    def validate_drive_start(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Drive start time must include a timezone.")
        if value <= datetime.now(timezone.utc):
            raise ValueError("Drive start time must be in the future.")
        return value

class DriveOut(BaseModel):
    id: int
    organizer_id: int
    title: str
    description: str
    location_text: str
    starts_at: datetime
    capacity: int | None
    status: str
    participant_count: int = 0
    model_config = ConfigDict(from_attributes=True)

class MessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=2000)
    @field_validator("body")
    @classmethod
    def trim_body(cls, value: str) -> str:
        value = value.strip()
        if not value: raise ValueError("Message cannot be blank.")
        return value

class MessageOut(BaseModel):
    id: int
    task_id: int
    sender_id: int
    body: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class TaskProofOut(BaseModel):
    id: int
    task_id: int
    uploader_id: int
    proof_kind: str
    original_name: str
    content_type: str
    size_bytes: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class WorkerOut(BaseModel):
    id: int
    display_name: str
    locality: str
    purpose: str
    skills: list[str]
    tools: list[str] = Field(default_factory=list)
    created_at: datetime
