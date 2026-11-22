from datetime import datetime, timezone
from pathlib import Path
from io import BytesIO
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.database import Base, get_db
from app.main import app
from app.core.security import hash_secret
from app.models import User, Scan, ScanAttachment, Measurement, AgeResult, QualityEvaluation
from app.services.storage import resolve_storage_key

def _png(color):
    image = Image.new("RGB", (4, 4), color=color)
    buffer = BytesIO(); image.save(buffer, format="PNG")
    return buffer.getvalue()
PNG = _png((35, 55, 75))
PDF = b"%PDF-1.4\n% rice age test report\n%%EOF"

def payload(client_scan_id="TEST-SCAN-0038"):
    return {
        "schema_version":"1.0", "client_scan_id":client_scan_id, "device_id":"RICE-DEVICE-001",
        "sample":{"sample_id":"Sample-0038", "batch_id":"BATCH-2026-001", "lot_id":"LOT-A"},
        "analyzed_at":"2026-11-20T16:37:52+05:30",
        "analysis":{"grain_count":363,"sample_mass_est_g":8.87,"avg_length_mm":5.25,"avg_breadth_mm":2.61,
                     "quality_parameters":[{"code":"HEAD_RICE","mass_percent":50.68,"count_percent":39.94,"status":"FLAG"}]},
        "rice_age":{"value": "8-10", "unit":"months", "category":"8-10 Months", "confidence_percent":100, "validation_status":"DEVICE_REPORTED"},
        "evaluation":{"overall":"FLAG", "ruleset_version":"sample-v1", "certification_status":"ADVISORY_ONLY"},
        "attachments":["REPORT_PDF","BOTTOM_PLATEN","TOP_PLATEN"]
    }

def _upload_all(client, headers, scan_id):
    for role, content, mime in [
        ("REPORT_PDF", PDF, "application/pdf"),
        ("BOTTOM_PLATEN", PNG, "image/png"),
        ("TOP_PLATEN", _png((55, 75, 95)), "image/png"),
    ]:
        response = client.put(f"/api/v1/device/scans/{scan_id}/attachments/{role}", headers=headers,
                              files={"file":(f"{role.lower()}.{ 'pdf' if role == 'REPORT_PDF' else 'png'}", content, mime)})
        assert response.status_code == 200, response.text

def test_end_to_end_ingestion_private_files_and_department_isolation(client, admin_headers, registered_device, tmp_path):
    device_headers = registered_device["headers"]
    submitted = client.post("/api/v1/device/scans", headers=device_headers, json=payload())
    assert submitted.status_code == 201, submitted.text
    scan_id = submitted.json()["scan_id"]
    assert submitted.json()["processing_status"] == "Awaiting Files"

    # Cannot finalize before all required files have been verified.
    early = client.post(f"/api/v1/device/scans/{scan_id}/finalize", headers=device_headers)
    assert early.status_code == 409

    _upload_all(client, device_headers, scan_id)
    finalized = client.post(f"/api/v1/device/scans/{scan_id}/finalize", headers=device_headers)
    assert finalized.status_code == 200, finalized.text
    assert finalized.json()["processing_status"] == "Completed"
    assert finalized.json()["department_id"] == registered_device["department_id"]

    # Exact replay is safe and does not create a second scan.
    replay = client.post("/api/v1/device/scans", headers=device_headers, json=payload())
    assert replay.status_code == 201
    assert replay.json()["replayed"] is True
    assert replay.json()["scan_id"] == scan_id

    # Verify relational scan/measurement/age/quality/file records and physical private storage.
    db = client.app.state.test_session_factory()
    saved_scan = db.get(Scan, scan_id)
    assert saved_scan is not None and saved_scan.processing_status == "Completed"
    assert saved_scan.department_id == registered_device["department_id"]
    assert db.query(Measurement).filter(Measurement.scan_id == scan_id).count() >= 4
    assert db.query(QualityEvaluation).filter(QualityEvaluation.scan_id == scan_id).count() == 1
    assert db.query(AgeResult).filter(AgeResult.scan_id == scan_id).count() == 1
    stored_files = db.query(ScanAttachment).filter(ScanAttachment.scan_id == scan_id).all()
    assert {x.role for x in stored_files} == {"REPORT_PDF", "BOTTOM_PLATEN", "TOP_PLATEN"}
    for stored in stored_files:
        assert resolve_storage_key(stored.storage_key).is_file()
    db.close()
    # Same-department authorized user can read; another department cannot.
    user_a = client.post("/api/v1/admin/users", headers=admin_headers, json={"email":"a@example.com","full_name":"Dept A User","password":"Department-A-Password!","role":"DEPARTMENT_USER","department_id":registered_device["department_id"]})
    assert user_a.status_code == 201, user_a.text
    dept_b = client.post("/api/v1/admin/departments", headers=admin_headers, json={"code":"DEPT-B","name":"Department B"})
    user_b = client.post("/api/v1/admin/users", headers=admin_headers, json={"email":"b@example.com","full_name":"Dept B User","password":"Department-B-Password!","role":"DEPARTMENT_USER","department_id":dept_b.json()["id"]})
    token_a = client.post("/api/v1/auth/login", json={"email":"a@example.com","password":"Department-A-Password!"}).json()["access_token"]
    token_b = client.post("/api/v1/auth/login", json={"email":"b@example.com","password":"Department-B-Password!"}).json()["access_token"]
    a_headers = {"Authorization":f"Bearer {token_a}"}; b_headers={"Authorization":f"Bearer {token_b}"}
    allowed = client.get(f"/api/v1/scans/{scan_id}", headers=a_headers)
    assert allowed.status_code == 200
    assert allowed.json()["department_id"] == registered_device["department_id"]
    allowed_file = client.get(f"/api/v1/scans/{scan_id}/files/REPORT_PDF", headers=a_headers)
    assert allowed_file.status_code == 200
    assert allowed_file.content == PDF
    denied = client.get(f"/api/v1/scans/{scan_id}", headers=b_headers)
    assert denied.status_code == 404
    denied_file = client.get(f"/api/v1/scans/{scan_id}/files/REPORT_PDF", headers=b_headers)
    assert denied_file.status_code == 404


def test_conflicting_duplicate_is_rejected(client, registered_device):
    headers = registered_device["headers"]
    first = client.post("/api/v1/device/scans", headers=headers, json=payload("DUPLICATE-1"))
    assert first.status_code == 201
    changed = payload("DUPLICATE-1")
    changed["analysis"]["grain_count"] = 999
    second = client.post("/api/v1/device/scans", headers=headers, json=changed)
    assert second.status_code == 409


def test_device_payload_cannot_impersonate_another_device(client, registered_device):
    headers = registered_device["headers"]
    altered = payload("IMPERSONATION-1")
    altered["device_id"] = "OTHER-DEVICE"
    response = client.post("/api/v1/device/scans", headers=headers, json=altered)
    assert response.status_code == 403


def test_device_reassignment_preserves_existing_scan_department(client, admin_headers, registered_device):
    headers = registered_device["headers"]
    first = client.post("/api/v1/device/scans", headers=headers, json=payload("BEFORE-REASSIGN"))
    scan_id = first.json()["scan_id"]
    old_department = registered_device["department_id"]
    new_department = client.post("/api/v1/admin/departments", headers=admin_headers, json={"code":"DEPT-C","name":"Department C"}).json()["id"]
    moved = client.post(f"/api/v1/admin/devices/{registered_device['device_id']}/reassign", headers=admin_headers, params={"department_id":new_department})
    assert moved.status_code == 200
    # A new token is not necessary: token identifies the device; server resolves current mapping at scan acceptance.
    next_payload = payload("AFTER-REASSIGN")
    next_payload["sample"]["sample_id"] = "Sample-after"
    second = client.post("/api/v1/device/scans", headers=headers, json=next_payload)
    assert second.status_code == 201
    # Department snapshot of old and new records is established at ingestion time.
    old_read = client.get(f"/api/v1/scans/{scan_id}", headers=admin_headers)
    new_read = client.get(f"/api/v1/scans/{second.json()['scan_id']}", headers=admin_headers)
    assert old_read.json()["department_id"] == old_department
    assert new_read.json()["department_id"] == new_department

def test_device_credential_rotation_revokes_existing_tokens(client, admin_headers, registered_device):
    old_headers = registered_device["headers"]
    rotated = client.post(f"/api/v1/admin/devices/{registered_device['device_id']}/rotate-credential", headers=admin_headers)
    assert rotated.status_code == 200
    old_token = client.get("/api/v1/device-auth/identity", headers=old_headers)
    assert old_token.status_code == 401
    new_token = client.post("/api/v1/device-auth/token", json={"device_id":registered_device["device_id"], "device_secret":rotated.json()["device_secret"]})
    assert new_token.status_code == 200
    identity = client.get("/api/v1/device-auth/identity", headers={"Authorization":f"Bearer {new_token.json()['access_token']}"})
    assert identity.status_code == 200
