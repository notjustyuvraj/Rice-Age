from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import current_device
from app.core.config import settings
from app.core.security import verify_secret, create_access_token
from app.db.database import get_db
from app.models import Device, DeviceAssignment, AuditLog
from app.schemas.contracts import DeviceAuthRequest, DeviceTokenResponse

router = APIRouter(prefix="/device-auth", tags=["Device authentication"])

@router.post("/token", response_model=DeviceTokenResponse)
def device_token(body: DeviceAuthRequest, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.device_id == body.device_id).first()
    if not device or device.status not in ("PENDING_ENROLLMENT", "ACTIVE") or not verify_secret(body.device_secret, device.credential_hash):
        raise HTTPException(401, "Invalid device credentials")
    department = db.query(DeviceAssignment).filter(DeviceAssignment.device_id == device.id, DeviceAssignment.effective_to.is_(None)).first()
    if not department or department.department_id != device.assigned_department_id:
        raise HTTPException(403, "Device has no valid active department assignment")
    first_activation = device.status == "PENDING_ENROLLMENT"
    device.status = "ACTIVE"  # First valid device authentication completes enrollment.
    if first_activation:
        db.add(AuditLog(actor_type="DEVICE", actor_id=device.device_id, action="DEVICE_ACTIVATED", target_type="device", target_id=device.device_id, details={"department_id": device.assigned_department_id}))
    device.last_heartbeat_at = datetime.now(timezone.utc)
    db.commit()
    return DeviceTokenResponse(access_token=create_access_token(device.device_id, "device", settings.device_token_minutes, {"device_db_id": device.id, "credential_version": device.credential_version}), expires_in=settings.device_token_minutes * 60, device_id=device.device_id)

@router.get("/identity")
def device_identity(device: Device = Depends(current_device)):
    return {"device_id": device.device_id, "department_id": device.assigned_department_id, "status": device.status}
