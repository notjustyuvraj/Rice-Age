"""Submit one simulated rice scan through the P2 device API."""
import argparse, os
from io import BytesIO
from pathlib import Path
import httpx
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
def make_test_png(color: tuple[int, int, int]) -> bytes:
    image = Image.new("RGB", (320, 180), color=color)
    buffer = BytesIO(); image.save(buffer, format="PNG")
    return buffer.getvalue()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=os.getenv("RICE_AGE_API", "http://localhost:8000"))
    parser.add_argument("--device-id", default=os.getenv("RICE_AGE_DEVICE_ID", "RICE-DEVICE-001"))
    parser.add_argument("--device-secret", default=os.getenv("RICE_AGE_DEVICE_SECRET"))
    parser.add_argument("--pdf", default=str(ROOT / "docs/reference/APSCSCL_Quality_Certificate_Sample-0038.pdf"))
    parser.add_argument("--scan-id", default="SIM-SCAN-0038-FULL")
    args = parser.parse_args()
    if not args.device_secret:
        parser.error("Provide --device-secret or RICE_AGE_DEVICE_SECRET")
    pdf = Path(args.pdf)
    if not pdf.is_file(): parser.error(f"PDF not found: {pdf}")
    payload = {
        "schema_version": "1.0", "client_scan_id": args.scan_id, "device_id": args.device_id,
        "sample": {"sample_id": "Sample-0038", "batch_id": "BATCH-2026-001", "lot_id": "LOT-A"},
        "analyzed_at": "2026-11-20T16:37:52+05:30",
        "analysis": {
            "grain_count": 363, "sample_mass_est_g": 8.87, "avg_length_mm": 5.25, "avg_breadth_mm": 2.61,
            "grain_shape_ratio": 2.01, "grain_shape_label": "Short Bold", "unresolved_clusters": 0,
            "quality_parameters": [
                {"code":"HEAD_RICE", "name":"Head Rice (Whole Kernels >= 75%)", "permissible_limit":"Min 75.00%", "mass_percent":50.68, "count_percent":39.94, "kernel_count":145, "estimated_mass_g":4.496, "status":"FLAG"},
                {"code":"BIG_BROKEN", "name":"Big Broken Grains (25% - 75%)", "permissible_limit":"Max 15.00%", "mass_percent":30.68, "count_percent":50.69, "kernel_count":184, "estimated_mass_g":2.721, "status":"FLAG"},
                {"code":"SMALL_BROKEN", "name":"Small Broken Grains (< 25% Fragments)", "permissible_limit":"Max 1.00%", "mass_percent":0.00, "count_percent":0.00, "kernel_count":0, "estimated_mass_g":0.000, "status":"PASS"},
                {"code":"TOTAL_BROKENS", "name":"Total Brokens (Big + Small)", "permissible_limit":"Max 16.00%", "mass_percent":30.68, "count_percent":50.69, "kernel_count":184, "estimated_mass_g":2.721, "status":"FLAG"},
                {"code":"FOREIGN_MATTER", "name":"Foreign Matter (Inorganic/Organic)", "permissible_limit":"Max 0.50%", "mass_percent":0.00, "count_percent":0.00, "kernel_count":0, "estimated_mass_g":0.000, "status":"PASS"},
                {"code":"DAMAGED_INSECT_INFESTED", "name":"Damaged & Insect-Infested Grains", "permissible_limit":"Max 2.00%", "mass_percent":0.00, "count_percent":0.00, "kernel_count":0, "estimated_mass_g":0.000, "status":"PASS"},
                {"code":"DISCOLOURED_AMBER", "name":"Discoloured / Amber Grains", "permissible_limit":"Max 1.00%", "mass_percent":0.00, "count_percent":0.00, "kernel_count":0, "estimated_mass_g":0.000, "status":"PASS"},
                {"code":"CHALKY_GRAINS", "name":"Chalky Grains (>= 50% Opacity)", "permissible_limit":"Max 3.00%", "mass_percent":0.00, "count_percent":0.00, "kernel_count":0, "estimated_mass_g":0.000, "status":"PASS"},
                {"code":"DEHUSKED_UNMILLED_PADDY", "name":"Dehusked / Unmilled Paddy Grains", "permissible_limit":"Max 10.00%", "mass_percent":0.00, "count_percent":0.00, "kernel_count":0, "estimated_mass_g":0.000, "status":"PASS"}
            ]
        },
        "rice_age": {
            "value":"8-10", "unit":"months", "category":"8-10 Months", "confidence_percent":100,
            "validation_status":"DEVICE_REPORTED", "sample_uniformity":"Uniform Age",
            "age_breakdown":"100% 8-10 Months",
            "freshness_rating":"Sound Commercial Grain (Medium Storage Age)",
            "testing_station":"Rice Age Chemical Unit (192.168.23.176:5000)",
            "color_reference_guide":[
                {"detected_color":"Green", "estimated_age":"1-2 Months", "status":"—", "color_hex":"#2f9b55"},
                {"detected_color":"Avocado Green", "estimated_age":"3-5 Months", "status":"—", "color_hex":"#719345"},
                {"detected_color":"Yellow", "estimated_age":"6-8 Months", "status":"—", "color_hex":"#e1c53c"},
                {"detected_color":"Yellow Orange", "estimated_age":"8-10 Months", "status":"ACTIVE 100%", "color_hex":"#e9a323"},
                {"detected_color":"Orange", "estimated_age":"10-11 Months", "status":"—", "color_hex":"#dc782c"},
                {"detected_color":"Red", "estimated_age":"Above 1 Year", "status":"—", "color_hex":"#c83b3b"}
            ]
        },
        "evaluation": {"overall":"FLAG", "ruleset_version":"sample-v1", "certification_status":"ADVISORY_ONLY"},
        "attachments": ["REPORT_PDF", "BOTTOM_PLATEN", "TOP_PLATEN"]
    }
    with httpx.Client(base_url=args.base_url, timeout=60) as client:
        auth = client.post("/api/v1/device-auth/token", json={"device_id":args.device_id, "device_secret":args.device_secret})
        auth.raise_for_status(); headers={"Authorization":f"Bearer {auth.json()['access_token']}"}
        submit = client.post("/api/v1/device/scans", headers=headers, json=payload); submit.raise_for_status()
        scan_id = submit.json()["scan_id"]
        print(f"Scan accepted: {scan_id} ({submit.json()['processing_status']}; replay={submit.json()['replayed']})")
        prep = client.post(f"/api/v1/device/scans/{scan_id}/attachments/prepare", headers=headers); prep.raise_for_status()
        attachments = [
            ("REPORT_PDF", pdf.read_bytes(), "application/pdf", f"{args.scan_id}.pdf"),
            ("BOTTOM_PLATEN", make_test_png((38, 48, 58)), "image/png", "bottom-platen.png"),
            ("TOP_PLATEN", make_test_png((58, 68, 78)), "image/png", "top-platen.png")
        ]
        for role, data, mime, filename in attachments:
            upload = client.put(f"/api/v1/device/scans/{scan_id}/attachments/{role}", headers=headers,
                                files={"file":(filename, data, mime)})
            upload.raise_for_status(); print(f"Uploaded {role}: {upload.json()['sha256']}")
        done = client.post(f"/api/v1/device/scans/{scan_id}/finalize", headers=headers); done.raise_for_status()
        print(f"Final state: {done.json()['processing_status']}; department={done.json()['department_id']}")
        status = client.get(f"/api/v1/device/scans/{scan_id}/status", headers=headers); status.raise_for_status()
        print(status.json())

if __name__ == "__main__": main()
