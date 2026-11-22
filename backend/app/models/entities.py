from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, Index, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base

def utcnow():
    return datetime.now(timezone.utc)

class Department(Base):
    __tablename__ = "departments"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(180))
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(180))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30), index=True)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    department: Mapped[Department | None] = relationship()

class Device(Base):
    __tablename__ = "devices"
    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    serial_number: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    friendly_name: Mapped[str | None] = mapped_column(String(180), nullable=True)
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    firmware_version: Mapped[str | None] = mapped_column(String(80), nullable=True)
    installation_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    assigned_department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), index=True)
    credential_hash: Mapped[str] = mapped_column(String(255))
    credential_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="PENDING_ENROLLMENT", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class DeviceAssignment(Base):
    __tablename__ = "device_assignments"
    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), index=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), index=True)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    changed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

class Scan(Base):
    __tablename__ = "scans"
    __table_args__ = (
        UniqueConstraint("device_id", "client_scan_id", name="uq_scan_device_client_id"),
        Index("ix_scans_department_analyzed", "department_id", "analyzed_at"),
        Index("ix_scans_department_batch", "department_id", "batch_id"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    device_db_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), index=True)
    device_id: Mapped[str] = mapped_column(String(100), index=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), index=True)  # ownership snapshot
    client_scan_id: Mapped[str] = mapped_column(String(150))
    sample_id: Mapped[str] = mapped_column(String(150), index=True)
    batch_id: Mapped[str | None] = mapped_column(String(150), nullable=True, index=True)
    lot_id: Mapped[str | None] = mapped_column(String(150), nullable=True, index=True)
    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    processing_status: Mapped[str] = mapped_column(String(30), default="Received", index=True)
    quality_verdict: Mapped[str | None] = mapped_column(String(40), nullable=True)
    payload_hash: Mapped[str] = mapped_column(String(64))
    raw_payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class Measurement(Base):
    __tablename__ = "measurements"
    id: Mapped[int] = mapped_column(primary_key=True)
    scan_id: Mapped[int] = mapped_column(ForeignKey("scans.id", ondelete="CASCADE"), index=True)
    metric_code: Mapped[str] = mapped_column(String(120), index=True)
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(60), nullable=True)
    basis: Mapped[str | None] = mapped_column(String(60), nullable=True)
    measured_vs_estimated: Mapped[str | None] = mapped_column(String(30), nullable=True)
    source_path: Mapped[str] = mapped_column(String(255))
    details: Mapped[dict] = mapped_column(JSON, default=dict)

class AgeResult(Base):
    __tablename__ = "age_results"
    id: Mapped[int] = mapped_column(primary_key=True)
    scan_id: Mapped[int] = mapped_column(ForeignKey("scans.id", ondelete="CASCADE"), unique=True, index=True)
    age_value: Mapped[str | None] = mapped_column(String(100), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    category: Mapped[str | None] = mapped_column(String(120), nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    validation_status: Mapped[str | None] = mapped_column(String(80), nullable=True)
    raw_result: Mapped[dict] = mapped_column(JSON, default=dict)

class QualityEvaluation(Base):
    __tablename__ = "quality_evaluations"
    id: Mapped[int] = mapped_column(primary_key=True)
    scan_id: Mapped[int] = mapped_column(ForeignKey("scans.id", ondelete="CASCADE"), index=True)
    parameter_code: Mapped[str] = mapped_column(String(120), index=True)
    parameter_name: Mapped[str | None] = mapped_column(String(180), nullable=True)
    permissible_limit: Mapped[str | None] = mapped_column(String(120), nullable=True)
    mass_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    count_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    kernel_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_mass_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str | None] = mapped_column(String(60), nullable=True)
    ruleset_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    raw_result: Mapped[dict] = mapped_column(JSON, default=dict)

class UploadAttempt(Base):
    __tablename__ = "upload_attempts"
    id: Mapped[int] = mapped_column(primary_key=True)
    scan_id: Mapped[int] = mapped_column(ForeignKey("scans.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(40))
    diagnostic_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ScanAttachment(Base):
    __tablename__ = "scan_attachments"
    __table_args__ = (UniqueConstraint("scan_id", "role", name="uq_attachment_scan_role"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    scan_id: Mapped[int] = mapped_column(ForeignKey("scans.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(40))
    storage_key: Mapped[str] = mapped_column(String(500), unique=True)
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_type: Mapped[str] = mapped_column(String(30))
    actor_id: Mapped[str] = mapped_column(String(120))
    action: Mapped[str] = mapped_column(String(120), index=True)
    target_type: Mapped[str] = mapped_column(String(80))
    target_id: Mapped[str] = mapped_column(String(120))
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
