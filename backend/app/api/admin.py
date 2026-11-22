import secrets
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import require_roles
from app.core.security import hash_secret
from app.db.database import get_db
from app.models import Department, User, Device, DeviceAssignment, AuditLog
from app.schemas.contracts import DepartmentCreate, DepartmentOut, UserCreate, UserOut, DeviceCreate

router = APIRouter(prefix="/admin", tags=["Administration"])

@router.post("/departments", response_model=DepartmentOut, status_code=201)
def create_department(body: DepartmentCreate, db: Session = Depends(get_db), actor: User = Depends(require_roles("SUPER_ADMIN"))):
    if db.query(Department).filter(Department.code == body.code.upper()).first(): raise HTTPException(409, "Department code already exists")
    dept = Department(code=body.code.upper(), name=body.name, location=body.location)
    db.add(dept); db.flush()
    db.add(AuditLog(actor_type="USER", actor_id=str(actor.id), action="DEPARTMENT_CREATED", target_type="department", target_id=str(dept.id), details={"code": dept.code}))
    db.commit(); db.refresh(dept)
    return dept

@router.get("/departments", response_model=list[DepartmentOut])
def list_departments(db: Session = Depends(get_db), actor: User = Depends(require_roles("SUPER_ADMIN"))):
    return db.query(Department).order_by(Department.name).all()

@router.post("/users", response_model=UserOut, status_code=201)
def create_user(body: UserCreate, db: Session = Depends(get_db), actor: User = Depends(require_roles("SUPER_ADMIN", "DEPARTMENT_ADMIN"))):
    if db.query(User).filter(User.email == body.email.lower()).first(): raise HTTPException(409, "Email already registered")
    if body.role == "SUPER_ADMIN":
        if actor.role != "SUPER_ADMIN": raise HTTPException(403, "Only Super Admin can create Super Admins")
        if body.department_id is not None: raise HTTPException(422, "Super Admin cannot be assigned to a department")
    else:
        if body.department_id is None: raise HTTPException(422, "Department is required for departmental users")
        if actor.role == "DEPARTMENT_ADMIN" and actor.department_id != body.department_id: raise HTTPException(403, "Cannot manage users in another department")
        if not db.query(Department).filter(Department.id == body.department_id, Department.is_active.is_(True)).first(): raise HTTPException(404, "Active department not found")
        if actor.role == "DEPARTMENT_ADMIN" and body.role not in ("DEPARTMENT_ADMIN", "DEPARTMENT_USER"):
            raise HTTPException(403, "Role is not permitted")
    user = User(email=body.email.lower(), full_name=body.full_name, password_hash=hash_secret(body.password), role=body.role, department_id=body.department_id)
    db.add(user); db.flush()
    db.add(AuditLog(actor_type="USER", actor_id=str(actor.id), action="USER_CREATED", target_type="user", target_id=str(user.id), details={"role": user.role, "department_id": user.department_id}))
    db.commit(); db.refresh(user)
    return UserOut(id=user.id, email=user.email, full_name=user.full_name, role=user.role, department_id=user.department_id, is_active=user.is_active)

@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), actor: User = Depends(require_roles("SUPER_ADMIN", "DEPARTMENT_ADMIN"))):
    q = db.query(User)
    if actor.role == "DEPARTMENT_ADMIN": q = q.filter(User.department_id == actor.department_id)
    return [UserOut(id=u.id, email=u.email, full_name=u.full_name, role=u.role, department_id=u.department_id, is_active=u.is_active) for u in q.order_by(User.id).all()]

@router.post("/devices", status_code=201)
def register_device(body: DeviceCreate, db: Session = Depends(get_db), actor: User = Depends(require_roles("SUPER_ADMIN"))):
    if db.query(Device).filter((Device.device_id == body.device_id) | (Device.serial_number == body.serial_number)).first(): raise HTTPException(409, "Device ID or serial number already exists")
    department = db.get(Department, body.department_id)
    if not department or not department.is_active: raise HTTPException(404, "Active department not found")
    secret = secrets.token_urlsafe(32)
    device = Device(device_id=body.device_id, serial_number=body.serial_number, friendly_name=body.friendly_name, model=body.model, firmware_version=body.firmware_version, installation_location=body.installation_location, assigned_department_id=body.department_id, credential_hash=hash_secret(secret), status="PENDING_ENROLLMENT")
    db.add(device); db.flush()
    db.add(DeviceAssignment(device_id=device.id, department_id=body.department_id, changed_by_user_id=actor.id))
    db.add(AuditLog(actor_type="USER", actor_id=str(actor.id), action="DEVICE_REGISTERED", target_type="device", target_id=device.device_id, details={"department_id": body.department_id}))
    db.commit(); db.refresh(device)
    return {"device": {"id": device.id, "device_id": device.device_id, "serial_number": device.serial_number, "assigned_department_id": device.assigned_department_id, "status": device.status}, "device_secret": secret, "warning": "Save this secret now. It is displayed only once."}

@router.get("/devices")
def list_devices(db: Session = Depends(get_db), actor: User = Depends(require_roles("SUPER_ADMIN", "DEPARTMENT_ADMIN"))):
    q = db.query(Device)
    if actor.role == "DEPARTMENT_ADMIN": q = q.filter(Device.assigned_department_id == actor.department_id)
    return [{"id": d.id, "device_id": d.device_id, "serial_number": d.serial_number, "assigned_department_id": d.assigned_department_id, "status": d.status, "friendly_name": d.friendly_name} for d in q.order_by(Device.id).all()]

@router.post("/devices/{device_id}/reassign")
def reassign_device(device_id: str, department_id: int, db: Session = Depends(get_db), actor: User = Depends(require_roles("SUPER_ADMIN"))):
    device = db.query(Device).filter(Device.device_id == device_id).first()
    dept = db.get(Department, department_id)
    if not device: raise HTTPException(404, "Device not found")
    if not dept or not dept.is_active: raise HTTPException(404, "Active department not found")
    if device.assigned_department_id == department_id: return {"device_id": device_id, "department_id": department_id, "changed": False}
    now = datetime.now(timezone.utc)
    active = db.query(DeviceAssignment).filter(DeviceAssignment.device_id == device.id, DeviceAssignment.effective_to.is_(None)).first()
    if active: active.effective_to = now
    db.add(DeviceAssignment(device_id=device.id, department_id=department_id, effective_from=now, changed_by_user_id=actor.id))
    old_department = device.assigned_department_id
    device.assigned_department_id = department_id
    db.add(AuditLog(actor_type="USER", actor_id=str(actor.id), action="DEVICE_REASSIGNED", target_type="device", target_id=device.device_id, details={"from_department_id": old_department, "to_department_id": department_id}))
    db.commit()
    return {"device_id": device_id, "department_id": department_id, "changed": True}

@router.post("/devices/{device_id}/suspend")
def suspend_device(device_id: str, db: Session = Depends(get_db), actor: User = Depends(require_roles("SUPER_ADMIN"))):
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device: raise HTTPException(404, "Device not found")
    device.status = "SUSPENDED"
    db.add(AuditLog(actor_type="USER", actor_id=str(actor.id), action="DEVICE_SUSPENDED", target_type="device", target_id=device.device_id, details={}))
    db.commit(); return {"device_id": device_id, "status": device.status}

@router.post("/devices/{device_id}/rotate-credential")
def rotate_device_credential(device_id: str, db: Session = Depends(get_db), actor: User = Depends(require_roles("SUPER_ADMIN"))):
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device: raise HTTPException(404, "Device not found")
    secret = secrets.token_urlsafe(32); device.credential_hash = hash_secret(secret); device.credential_version += 1
    db.add(AuditLog(actor_type="USER", actor_id=str(actor.id), action="DEVICE_CREDENTIAL_ROTATED", target_type="device", target_id=device.device_id, details={}))
    db.commit(); return {"device_id": device_id, "device_secret": secret, "warning": "Save this secret now. It is displayed only once."}
