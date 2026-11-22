import hashlib, json, re
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.api.deps import current_device, current_user
from app.core.config import settings
from app.db.database import get_db
from app.models import Device, Scan, ScanAttachment, User, AuditLog, Measurement, AgeResult, QualityEvaluation, UploadAttempt
from app.schemas.contracts import ScanSubmission, ScanAccepted, ScanStatus
from app.services.storage import store_upload, resolve_storage_key

router = APIRouter(tags=["IoT scan ingestion"])
REQUIRED_ROLES = {"REPORT_PDF", "BOTTOM_PLATEN", "TOP_PLATEN"}

def _persist_normalized_results(db: Session, scan: Scan, payload: dict) -> None:
    """Persist analyzable numeric values while retaining the complete immutable source JSON."""
    analysis = payload.get("analysis") or {}
    def walk(obj, prefix="analysis"):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == "quality_parameters":
                    continue
                yield from walk(value, f"{prefix}.{key}")
        elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
            leaf = prefix.rsplit(".", 1)[-1]
            unit = "mm" if leaf.endswith("_mm") else "g" if leaf.endswith("_g") else "kernels" if "count" in leaf else "%" if leaf.endswith("_percent") else None
            basis = "count" if "count" in leaf else "estimated_mass" if "mass_percent" in leaf or "est" in leaf else None
            estimate = "ESTIMATED" if "est" in leaf or "estimated" in prefix else "DEVICE_REPORTED"
            yield (prefix, float(obj), unit, basis, estimate)
    for source_path, value, unit, basis, estimate in walk(analysis):
        db.add(Measurement(scan_id=scan.id, metric_code=source_path.rsplit(".", 1)[-1].upper(), value=value, unit=unit, basis=basis, measured_vs_estimated=estimate, source_path=source_path, details={}))
    evaluation = payload.get("evaluation") or {}
    for item in analysis.get("quality_parameters", []) if isinstance(analysis, dict) else []:
        code = str(item.get("code") or item.get("parameter_code") or item.get("name") or "UNKNOWN").upper().replace(" ", "_")
        mass = item.get("mass_percent")
        count = item.get("count_percent")
        db.add(QualityEvaluation(scan_id=scan.id, parameter_code=code, parameter_name=item.get("name"),
            permissible_limit=str(item.get("permissible_limit")) if item.get("permissible_limit") is not None else None,
            mass_percent=float(mass) if isinstance(mass, (int, float)) else None,
            count_percent=float(count) if isinstance(count, (int, float)) else None,
            kernel_count=int(item["kernel_count"]) if isinstance(item.get("kernel_count"), (int, float)) else None,
            estimated_mass_g=float(item["estimated_mass_g"]) if isinstance(item.get("estimated_mass_g"), (int, float)) else None,
            status=item.get("status"), ruleset_version=evaluation.get("ruleset_version"), raw_result=item))
        if isinstance(mass, (int, float)):
            db.add(Measurement(scan_id=scan.id, metric_code=f"{code}_MASS_PERCENT", value=float(mass), unit="%", basis="estimated_mass", measured_vs_estimated="ESTIMATED", source_path=f"analysis.quality_parameters.{code}.mass_percent", details={"parameter_code": code}))
        if isinstance(count, (int, float)):
            db.add(Measurement(scan_id=scan.id, metric_code=f"{code}_COUNT_PERCENT", value=float(count), unit="%", basis="count", measured_vs_estimated="DEVICE_REPORTED", source_path=f"analysis.quality_parameters.{code}.count_percent", details={"parameter_code": code}))
    age = payload.get("rice_age")
    if isinstance(age, dict):
        db.add(AgeResult(scan_id=scan.id, age_value=str(age.get("value")) if age.get("value") is not None else None,
            unit=age.get("unit"), category=age.get("category"), model_version=age.get("model_version") or age.get("method_version"),
            confidence=float(age["confidence_percent"]) if isinstance(age.get("confidence_percent"), (int, float)) else None,
            validation_status=age.get("validation_status"), raw_result=age))

@router.post("/device/scans", response_model=ScanAccepted, status_code=201)
def submit_scan(body: ScanSubmission, db: Session = Depends(get_db), device: Device = Depends(current_device)):
    if body.device_id != device.device_id:
        raise HTTPException(403, "Payload device_id does not match authenticated device")
    if settings.require_all_attachments and not REQUIRED_ROLES.issubset(set(body.attachments)):
        raise HTTPException(422, {"message": "Attachment manifest must include the original PDF and both platen images", "required": sorted(REQUIRED_ROLES)})
    if body.attachments and len(body.attachments) != len(set(body.attachments)):
        raise HTTPException(422, "Attachment manifest contains duplicate roles")
    payload = body.model_dump(mode="json")
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    digest = hashlib.sha256(canonical).hexdigest()
    existing = db.query(Scan).filter(Scan.device_db_id == device.id, Scan.client_scan_id == body.client_scan_id).first()
    if existing:
        if existing.payload_hash != digest:
            raise HTTPException(409, "client_scan_id already exists with a different payload")
        return ScanAccepted(scan_id=existing.id, client_scan_id=existing.client_scan_id, processing_status=existing.processing_status, replayed=True)
    scan = Scan(device_db_id=device.id, device_id=device.device_id, department_id=device.assigned_department_id,
                client_scan_id=body.client_scan_id, sample_id=body.sample.sample_id,
                batch_id=body.sample.batch_id, lot_id=body.sample.lot_id,
                analyzed_at=body.analyzed_at, processing_status="Received",
                quality_verdict=(body.evaluation or {}).get("overall"), payload_hash=digest, raw_payload=payload)
    db.add(scan)
    try:
        db.flush()
        _persist_normalized_results(db, scan, payload)
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.query(Scan).filter(Scan.device_db_id == device.id, Scan.client_scan_id == body.client_scan_id).first()
        if existing and existing.payload_hash == digest:
            return ScanAccepted(scan_id=existing.id, client_scan_id=existing.client_scan_id, processing_status=existing.processing_status, replayed=True)
        raise HTTPException(409, "Conflicting scan submission")
    db.refresh(scan)
    scan.processing_status = "Awaiting Files"
    db.commit()
    return ScanAccepted(scan_id=scan.id, client_scan_id=scan.client_scan_id, processing_status=scan.processing_status)

@router.post("/device/scans/{scan_id}/attachments/prepare")
def prepare_attachments(scan_id: int, db: Session = Depends(get_db), device: Device = Depends(current_device)):
    scan = db.query(Scan).filter(Scan.id == scan_id, Scan.device_db_id == device.id).first()
    if not scan: raise HTTPException(404, "Scan not found")
    if scan.processing_status in ("Completed", "Failed"): raise HTTPException(409, "Scan no longer accepts attachments")
    return {"scan_id": scan.id, "upload_roles": scan.raw_payload.get("attachments", []), "max_upload_bytes": settings.max_upload_bytes,
            "upload_endpoint_template": f"/api/v1/device/scans/{scan.id}/attachments/{{role}}"}

@router.put("/device/scans/{scan_id}/attachments/{role}")
async def upload_attachment(scan_id: int, role: str, file: UploadFile = File(...), db: Session = Depends(get_db), device: Device = Depends(current_device)):
    role = role.upper()
    scan = db.query(Scan).filter(Scan.id == scan_id, Scan.device_db_id == device.id).first()
    if not scan: raise HTTPException(404, "Scan not found")
    if scan.processing_status in ("Completed", "Failed"): raise HTTPException(409, "Scan no longer accepts attachments")
    manifest = set(scan.raw_payload.get("attachments", []))
    if role not in manifest: raise HTTPException(422, "Attachment role is not present in the submitted manifest")
    previous = db.query(ScanAttachment).filter(ScanAttachment.scan_id == scan.id, ScanAttachment.role == role).first()
    try:
        storage_key, content_type, size_bytes, digest = await store_upload(file, role)
    except HTTPException as exc:
        db.add(UploadAttempt(scan_id=scan.id, role=role, status="REJECTED", diagnostic_code=f"HTTP_{exc.status_code}"))
        db.commit()
        raise
    if previous:
        try: resolve_storage_key(storage_key).unlink(missing_ok=True)
        except Exception: pass
        if previous.sha256 == digest:
            return {"scan_id": scan.id, "role": role, "verified": previous.verified, "replayed": True, "sha256": digest}
        raise HTTPException(409, "A different attachment is already stored for this role")
    record = ScanAttachment(scan_id=scan.id, role=role, storage_key=storage_key, content_type=content_type, size_bytes=size_bytes, sha256=digest, verified=True)
    db.add(record)
    db.add(UploadAttempt(scan_id=scan.id, role=role, status="VERIFIED", diagnostic_code=None))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        try: resolve_storage_key(storage_key).unlink(missing_ok=True)
        except Exception: pass
        raise HTTPException(409, "Attachment upload conflicted with another request")
    return {"scan_id": scan.id, "role": role, "verified": True, "replayed": False, "size_bytes": size_bytes, "sha256": digest}

@router.post("/device/scans/{scan_id}/finalize", response_model=ScanStatus)
def finalize_scan(scan_id: int, db: Session = Depends(get_db), device: Device = Depends(current_device)):
    scan = db.query(Scan).filter(Scan.id == scan_id, Scan.device_db_id == device.id).first()
    if not scan: raise HTTPException(404, "Scan not found")
    if scan.processing_status == "Completed":
        records = db.query(ScanAttachment).filter(ScanAttachment.scan_id == scan.id).all()
        roles = [a.role for a in records if a.verified]
        return ScanStatus(scan_id=scan.id, client_scan_id=scan.client_scan_id, processing_status=scan.processing_status, department_id=scan.department_id, attachments_verified=roles, missing_attachments=sorted(REQUIRED_ROLES - set(roles)))
    if scan.processing_status == "Failed": raise HTTPException(409, "Failed scan cannot be finalized")
    records = db.query(ScanAttachment).filter(ScanAttachment.scan_id == scan.id).all()
    verified_roles = {a.role for a in records if a.verified}
    manifest = set(scan.raw_payload.get("attachments", []))
    required = REQUIRED_ROLES if settings.require_all_attachments else manifest
    missing = sorted(required - verified_roles)
    if missing:
        scan.processing_status = "Awaiting Files"
        db.commit()
        raise HTTPException(409, {"message": "Required attachments are missing or unverified", "missing_attachments": missing})
    if not required.issubset(manifest): raise HTTPException(422, "Manifest must declare every required attachment role")
    scan.processing_status = "Verifying"
    db.flush()
    # Recheck file presence, size, signature and SHA-256 immediately before completion.
    for attachment in records:
        try:
            file_path = resolve_storage_key(attachment.storage_key)
            data = file_path.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            from app.services.storage import validate_signature
            if (not attachment.verified or len(data) != attachment.size_bytes or
                    digest != attachment.sha256 or not validate_signature(attachment.role, data, attachment.content_type)):
                raise ValueError("stored attachment integrity mismatch")
        except (FileNotFoundError, OSError, ValueError):
            db.rollback()
            raise HTTPException(409, {"message": "Attachment integrity verification failed", "role": attachment.role})
    scan.processing_status = "Completed"
    scan.completed_at = datetime.now(timezone.utc)
    device.last_heartbeat_at = datetime.now(timezone.utc)
    db.add(AuditLog(actor_type="DEVICE", actor_id=device.device_id, action="SCAN_COMPLETED", target_type="scan", target_id=str(scan.id), details={"department_id": scan.department_id, "quality_verdict": scan.quality_verdict}))
    db.commit()
    return ScanStatus(scan_id=scan.id, client_scan_id=scan.client_scan_id, processing_status=scan.processing_status, department_id=scan.department_id, attachments_verified=sorted(verified_roles), missing_attachments=[])

@router.get("/device/scans/{scan_id}/status")
def device_scan_status(scan_id: int, db: Session = Depends(get_db), device: Device = Depends(current_device)):
    scan = db.query(Scan).filter(Scan.id == scan_id, Scan.device_db_id == device.id).first()
    if not scan: raise HTTPException(404, "Scan not found")
    roles = [a.role for a in db.query(ScanAttachment).filter(ScanAttachment.scan_id == scan.id, ScanAttachment.verified.is_(True)).all()]
    return {"scan_id": scan.id, "client_scan_id": scan.client_scan_id, "processing_status": scan.processing_status, "attachments_verified": roles, "missing_attachments": sorted(REQUIRED_ROLES - set(roles))}

# Minimal protected metadata/file endpoints exist to verify the P2 authorization boundary.
# They are APIs only; no reports UI, history UI or dashboard is included in this milestone.
@router.get("/scans/{scan_id}")
def protected_scan_metadata(scan_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    scan = db.get(Scan, scan_id)
    if not scan: raise HTTPException(404, "Scan not found")
    if user.role != "SUPER_ADMIN" and user.department_id != scan.department_id: raise HTTPException(404, "Scan not found")
    return {"id": scan.id, "sample_id": scan.sample_id, "batch_id": scan.batch_id, "lot_id": scan.lot_id, "device_id": scan.device_id,
            "department_id": scan.department_id, "processing_status": scan.processing_status, "quality_verdict": scan.quality_verdict,
            "analyzed_at": scan.analyzed_at.isoformat(), "attachments": [a.role for a in db.query(ScanAttachment).filter(ScanAttachment.scan_id == scan.id).all()]}

@router.get("/scans/{scan_id}/files/{role}")
def protected_scan_file(scan_id: int, role: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    scan = db.get(Scan, scan_id)
    if not scan: raise HTTPException(404, "Scan not found")
    if user.role != "SUPER_ADMIN" and user.department_id != scan.department_id: raise HTTPException(404, "File not found")
    attachment = db.query(ScanAttachment).filter(ScanAttachment.scan_id == scan_id, ScanAttachment.role == role.upper()).first()
    if not attachment: raise HTTPException(404, "File not found")
    try: path = resolve_storage_key(attachment.storage_key)
    except FileNotFoundError: raise HTTPException(404, "File not found")
    safe_scan_id = re.sub(r"[^A-Za-z0-9._-]", "_", scan.client_scan_id)[:100]
    extension = "pdf" if attachment.content_type == "application/pdf" else ("jpg" if attachment.content_type == "image/jpeg" else "png")
    return FileResponse(path, media_type=attachment.content_type, filename=f"{safe_scan_id}-{attachment.role.lower()}.{extension}", content_disposition_type="inline")
