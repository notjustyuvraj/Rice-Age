from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
import jwt
from app.db.database import get_db
from app.models import User, Device
from app.core.security import decode_token

bearer = HTTPBearer(auto_error=False)

def token_payload(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required", headers={"WWW-Authenticate": "Bearer"})
    try:
        return decode_token(credentials.credentials)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token", headers={"WWW-Authenticate": "Bearer"})

def current_user(payload: dict = Depends(token_payload), db: Session = Depends(get_db)) -> User:
    if payload.get("type") != "user": raise HTTPException(401, "Human user token required")
    user = db.get(User, int(payload["sub"]))
    if not user or not user.is_active: raise HTTPException(401, "User is inactive or no longer exists")
    return user

def current_device(payload: dict = Depends(token_payload), db: Session = Depends(get_db)) -> Device:
    if payload.get("type") != "device": raise HTTPException(401, "Device token required")
    device = db.query(Device).filter(Device.device_id == payload.get("sub")).first()
    if not device or device.status != "ACTIVE": raise HTTPException(401, "Device is inactive or no longer exists")
    if int(payload.get("device_db_id", -1)) != device.id: raise HTTPException(401, "Device identity mismatch")
    if int(payload.get("credential_version", -1)) != device.credential_version: raise HTTPException(401, "Device credentials have been rotated")
    return device

def require_roles(*roles: str):
    def dependency(user: User = Depends(current_user)) -> User:
        if user.role not in roles: raise HTTPException(403, "Insufficient permissions")
        return user
    return dependency
