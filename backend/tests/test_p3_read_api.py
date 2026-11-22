from io import BytesIO
from PIL import Image
from app.models import Scan, ScanAttachment


def _png(color):
    image = Image.new("RGB", (4, 4), color=color)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _payload(scan_id="P3-SCAN-0038"):
    return {
        "schema_version": "1.0", "client_scan_id": scan_id, "device_id": "RICE-DEVICE-001",
        "sample": {"sample_id": "Sample-0038", "batch_id": "BATCH-2026-001", "lot_id": "LOT-A"},
        "analyzed_at": "2026-11-20T16:37:52+05:30",
        "analysis": {"grain_count": 363, "sample_mass_est_g": 8.87, "avg_length_mm": 5.25,
                     "avg_breadth_mm": 2.61, "grain_shape_ratio": 2.01, "grain_shape_label": "Short Bold",
                     "unresolved_clusters": 0, "quality_parameters": [
                         {"code": "HEAD_RICE", "name": "Head Rice", "permissible_limit": "Min 75.00%",
                          "mass_percent": 50.68, "count_percent": 39.94, "kernel_count": 145,
                          "estimated_mass_g": 4.496, "status": "FLAG"},
                         {"code": "BIG_BROKEN", "name": "Big Broken Grains", "permissible_limit": "Max 15.00%",
                          "mass_percent": 30.68, "count_percent": 50.69, "kernel_count": 184,
                          "estimated_mass_g": 2.721, "status": "FLAG"},
                         {"code": "SMALL_BROKEN", "name": "Small Broken Grains", "permissible_limit": "Max 1.00%",
                          "mass_percent": 0.00, "count_percent": 0.00, "kernel_count": 0,
                          "estimated_mass_g": 0.000, "status": "PASS"},
                         {"code": "TOTAL_BROKENS", "name": "Total Brokens", "permissible_limit": "Max 16.00%",
                          "mass_percent": 30.68, "count_percent": 50.69, "kernel_count": 184,
                          "estimated_mass_g": 2.721, "status": "FLAG"},
                         {"code": "FOREIGN_MATTER", "name": "Foreign Matter", "permissible_limit": "Max 0.50%",
                          "mass_percent": 0.00, "count_percent": 0.00, "kernel_count": 0,
                          "estimated_mass_g": 0.000, "status": "PASS"},
                         {"code": "DAMAGED_INSECT_INFESTED", "name": "Damaged & Insect-Infested Grains", "permissible_limit": "Max 2.00%",
                          "mass_percent": 0.00, "count_percent": 0.00, "kernel_count": 0,
                          "estimated_mass_g": 0.000, "status": "PASS"},
                         {"code": "DISCOLOURED_AMBER", "name": "Discoloured / Amber Grains", "permissible_limit": "Max 1.00%",
                          "mass_percent": 0.00, "count_percent": 0.00, "kernel_count": 0,
                          "estimated_mass_g": 0.000, "status": "PASS"},
                         {"code": "CHALKY_GRAINS", "name": "Chalky Grains", "permissible_limit": "Max 3.00%",
                          "mass_percent": 0.00, "count_percent": 0.00, "kernel_count": 0,
                          "estimated_mass_g": 0.000, "status": "PASS"},
                         {"code": "DEHUSKED_UNMILLED_PADDY", "name": "Dehusked / Unmilled Paddy Grains", "permissible_limit": "Max 10.00%",
                          "mass_percent": 0.00, "count_percent": 0.00, "kernel_count": 0,
                          "estimated_mass_g": 0.000, "status": "PASS"}]},
        "rice_age": {"value": "8-10", "unit": "months", "category": "8-10 Months",
                     "confidence_percent": 100, "validation_status": "DEVICE_REPORTED",
                     "sample_uniformity": "Uniform Age", "age_breakdown": "100% 8-10 Months",
                     "freshness_rating": "Sound Commercial Grain (Medium Storage Age)",
                     "testing_station": "Rice Age Chemical Unit", "color_reference_guide": [
                         {"detected_color": "Yellow Orange", "estimated_age": "8-10 Months", "status": "ACTIVE 100%", "color_hex": "#e9a323"}]},
        "evaluation": {"overall": "FLAG", "ruleset_version": "sample-v1", "certification_status": "ADVISORY_ONLY"},
        "attachments": ["REPORT_PDF", "BOTTOM_PLATEN", "TOP_PLATEN"],
    }


def _complete(client, registered_device, scan_id="P3-SCAN-0038"):
    headers = registered_device["headers"]
    submitted = client.post("/api/v1/device/scans", headers=headers, json=_payload(scan_id))
    assert submitted.status_code == 201, submitted.text
    sid = submitted.json()["scan_id"]
    for role, data, mime, filename in [
        ("REPORT_PDF", b"%PDF-1.4\\nP3 fixture\\n%%EOF", "application/pdf", "report.pdf"),
        ("BOTTOM_PLATEN", _png((20, 40, 60)), "image/png", "bottom.png"),
        ("TOP_PLATEN", _png((60, 80, 100)), "image/png", "top.png"),
    ]:
        uploaded = client.put(f"/api/v1/device/scans/{sid}/attachments/{role}", headers=headers,
                              files={"file": (filename, data, mime)})
        assert uploaded.status_code == 200, uploaded.text
    finalized = client.post(f"/api/v1/device/scans/{sid}/finalize", headers=headers)
    assert finalized.status_code == 200, finalized.text
    return sid


def test_dashboard_latest_and_detail_are_department_scoped(client, admin_headers, registered_device):
    scan_id = _complete(client, registered_device)
    summary = client.get("/api/v1/dashboard/summary", headers=admin_headers)
    assert summary.status_code == 200, summary.text
    data = summary.json()
    assert data["counts"]["completed_scans"] == 1
    assert data["counts"]["flagged_scans"] == 1
    assert data["latest_scan"]["id"] == scan_id
    assert data["latest_scan"]["advisory_only"] is True

    latest = client.get("/api/v1/scans/latest", headers=admin_headers)
    assert latest.status_code == 200 and latest.json()["item"]["id"] == scan_id
    detail = client.get(f"/api/v1/scans/{scan_id}", headers=admin_headers)
    assert detail.status_code == 200, detail.text
    body = detail.json()
    assert body["quality_parameters"][0]["mass_percent"] == 50.68
    assert body["quality_parameters"][0]["count_percent"] == 39.94
    assert body["quality_parameters"][0]["estimated_mass_g"] == 4.496
    assert len(body["quality_parameters"]) == 9
    assert body["analysis"]["grain_shape_label"] == "Short Bold"
    assert body["rice_age_result"]["category"] == "8-10 Months"
    assert body["rice_age_result"]["freshness_rating"] == "Sound Commercial Grain (Medium Storage Age)"
    assert body["rice_age_result"]["color_reference_guide"][0]["status"] == "ACTIVE 100%"
    assert {a["role"] for a in body["attachments"]} == {"REPORT_PDF", "BOTTOM_PLATEN", "TOP_PLATEN"}


def test_scan_history_filters_and_latest_excludes_pending(client, admin_headers, registered_device):
    headers = registered_device["headers"]
    pending_payload = _payload("P3-PENDING")
    pending = client.post("/api/v1/device/scans", headers=headers, json=pending_payload)
    assert pending.status_code == 201
    no_latest_before_complete = client.get("/api/v1/scans/latest", headers=admin_headers)
    assert no_latest_before_complete.json()["item"] is None

    scan_id = _complete(client, registered_device)
    listed = client.get("/api/v1/scans?sample_id=0038&processing_status=Completed&page=1&page_size=5", headers=admin_headers)
    assert listed.status_code == 200, listed.text
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["id"] == scan_id
    assert listed.json()["pages"] == 1


def test_scan_history_ignores_department_override_for_department_user(client, admin_headers, registered_device):
    scan_id = _complete(client, registered_device, "P3-DEPT-SCOPE")
    dept_user = client.post("/api/v1/admin/users", headers=admin_headers, json={
        "email": "p3-dept@example.com", "full_name": "Department Reader", "password": "P3-Department-Password!",
        "role": "DEPARTMENT_USER", "department_id": registered_device["department_id"],
    })
    assert dept_user.status_code == 201, dept_user.text
    token = client.post("/api/v1/auth/login", json={"email": "p3-dept@example.com", "password": "P3-Department-Password!"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    other_dept = client.post("/api/v1/admin/departments", headers=admin_headers, json={"code": "P3-OTHER", "name": "Other Department"})
    summary = client.get(f"/api/v1/dashboard/summary?department_id={other_dept.json()['id']}", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["counts"]["completed_scans"] == 1
    listed = client.get(f"/api/v1/scans?department_id={other_dept.json()['id']}", headers=headers)
    assert listed.status_code == 200
    assert [x["id"] for x in listed.json()["items"]] == [scan_id]


def test_unverified_attachment_is_not_served(client, admin_headers, registered_device):
    submitted = client.post("/api/v1/device/scans", headers=registered_device["headers"], json=_payload("P3-UNVERIFIED"))
    assert submitted.status_code == 201, submitted.text
    scan_id = submitted.json()["scan_id"]
    db = client.app.state.test_session_factory()
    db.add(ScanAttachment(scan_id=scan_id, role="REPORT_PDF", storage_key="not-yet-verified/report.pdf",
                          content_type="application/pdf", size_bytes=100, sha256="0" * 64, verified=False))
    db.commit()
    db.close()
    response = client.get(f"/api/v1/scans/{scan_id}/files/REPORT_PDF", headers=admin_headers)
    assert response.status_code == 404
