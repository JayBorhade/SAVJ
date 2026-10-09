from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    display_name: str = Field(min_length=1, max_length=80)
    locality: str = Field(default="Pune, Maharashtra", min_length=1, max_length=160)
    purpose: str = Field(default="Both", pattern="^(Requester|Worker|Both)$")
    skills: list[str] = Field(default_factory=list, max_length=30)
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

class UserOut(BaseModel):
    id: int
    email: EmailStr
    display_name: str
    locality: str
    purpose: str
    skills: list[str]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut

class TaskCreate(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    description: str = Field(default="", max_length=4000)
    category: str = Field(default="Community cleanup", min_length=1, max_length=80)
    location_text: str = Field(min_length=2, max_length=200)
    budget_rupees: int = Field(ge=0, le=10000000)
    scheduled_at: datetime | None = None
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
    budget_minor_units: int
    currency: str
    status: str
    scheduled_at: datetime | None
    version: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DriveCreate(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    description: str = Field(default="", max_length=4000)
    location_text: str = Field(min_length=2, max_length=200)
    starts_at: datetime
    capacity: int | None = Field(default=None, ge=1, le=100000)

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
