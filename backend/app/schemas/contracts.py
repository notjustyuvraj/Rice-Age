from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

Role = Literal["SUPER_ADMIN", "DEPARTMENT_ADMIN", "DEPARTMENT_USER"]
AttachmentRole = Literal["REPORT_PDF", "BOTTOM_PLATEN", "TOP_PLATEN"]

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=180)
    password: str = Field(min_length=12, max_length=128)
    role: Role
    department_id: int | None = None

class DepartmentCreate(BaseModel):
    code: str = Field(min_length=2, max_length=40, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=2, max_length=180)
    location: str | None = Field(default=None, max_length=255)

class DeviceCreate(BaseModel):
    device_id: str = Field(min_length=3, max_length=100)
    serial_number: str = Field(min_length=3, max_length=120)
    department_id: int
    friendly_name: str | None = None
    model: str | None = None
    firmware_version: str | None = None
    installation_location: str | None = None

class DeviceAuthRequest(BaseModel):
    device_id: str
    device_secret: str

class DeviceTokenResponse(TokenResponse):
    device_id: str

class SampleIdentity(BaseModel):
    sample_id: str = Field(min_length=1, max_length=150)
    batch_id: str | None = Field(default=None, max_length=150)
    lot_id: str | None = Field(default=None, max_length=150)

class ScanSubmission(BaseModel):
    schema_version: str = Field(min_length=1, max_length=20)
    client_scan_id: str = Field(min_length=1, max_length=150)
    device_id: str = Field(min_length=1, max_length=100)
    sample: SampleIdentity
    analyzed_at: datetime
    analysis: dict[str, Any]
    rice_age: dict[str, Any] | None = None
    evaluation: dict[str, Any]
    attachments: list[AttachmentRole] = Field(min_length=1)

    @field_validator("analyzed_at")
    @classmethod
    def require_timezone(cls, value: datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("analyzed_at must include a timezone offset")
        return value

class ScanAccepted(BaseModel):
    scan_id: int
    client_scan_id: str
    processing_status: str
    replayed: bool = False

class ScanStatus(BaseModel):
    scan_id: int
    client_scan_id: str
    processing_status: str
    department_id: int
    attachments_verified: list[str]
    missing_attachments: list[str]

class DepartmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: str
    location: str | None
    is_active: bool

class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: str
    department_id: int | None
    is_active: bool

class DeviceOut(BaseModel):
    id: int
    device_id: str
    serial_number: str
    assigned_department_id: int
    status: str
    friendly_name: str | None
