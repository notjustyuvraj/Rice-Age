# Rice Age — P1/P2 Foundation & IoT Ingestion

See [Implementation Status](docs/IMPLEMENTATION_STATUS.md) for verified test results and remaining blockers.

This repository implements **only P1 and P2** from the supplied Rice Age SOR V5.0 and PRD V5.0: project foundation, PostgreSQL persistence, human authentication/RBAC, department and device administration, device authentication, secure scan ingestion, private PDF/image upload, verification/finalization, a simulated IoT client, and tests.

**Not included by design:** dashboard UI, scan-history UI, quality analytics, Rice Age dashboard, report UI, batch comparison, notifications, and frontend. The protected scan/file API endpoints are present only to exercise the P2 department-access boundary; they are not a user-facing report module.

## Implemented P1/P2 behavior

- Separate human (`SUPER_ADMIN`, `DEPARTMENT_ADMIN`, `DEPARTMENT_USER`) and machine (`device`) JWT identities.
- Passwords and device secrets are stored as salted scrypt hashes. Device secrets are shown only once at enrollment/rotation.
- Super Admin creates departments, users, devices, reassigns/suspends devices, and rotates device credentials. Department Admin can manage users within its own department.
- Each device has one active department assignment. Assignment history is retained. Each accepted scan stores an immutable department ownership snapshot.
- Device submits versioned JSON with an attachment manifest. Same `(device_id, client_scan_id)` and same payload is idempotent; conflicting replay returns HTTP 409.
- PDF, bottom platen image and top platen image are uploaded through authenticated device endpoints into private local storage. MIME, file signatures, size and SHA-256 are checked. No public static-file path is exposed.
- A scan remains `Awaiting Files` until all three required attachment roles are present and verified. Finalization then transitions through `Verifying` to `Completed`.
- Scan processing state is separate from the device-supplied quality verdict. No quality rule or age is inferred by the portal.

## Prerequisites

- Python 3.11+ (Docker image uses Python 3.12)
- Docker Desktop + Docker Compose plugin for PostgreSQL-backed local deployment
- Or Python plus PostgreSQL 15+ if running services separately

## Recommended run: Docker Compose

From the repository root:

```bash
cp .env.example .env
```

Edit `.env` and set a unique `SECRET_KEY`, strong bootstrap admin password, and PostgreSQL password. Then:

```bash
docker compose up --build -d
```

Check service health and API docs:

```bash
docker compose ps
curl http://localhost:8000/health
```

Open Swagger UI at `http://localhost:8000/docs`.

The API container automatically runs Alembic migrations and creates the first Super Admin if it does not exist. Development defaults are not suitable for production.

## Run backend without Docker (SQLite development mode)

SQLite is supported only as a convenient local development/test adapter. PostgreSQL is the target deployment database.

```bash
cd backend
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt
```

Set environment variables before running (PowerShell example):

```powershell
$env:DATABASE_URL="sqlite:///./rice_age_dev.db"
$env:SECRET_KEY="use-a-random-secret-with-at-least-32-characters"
$env:STORAGE_ROOT="../storage"
$env:BOOTSTRAP_ADMIN_EMAIL="admin@example.com"
$env:BOOTSTRAP_ADMIN_PASSWORD="ChangeMe-Immediately-123!"
```

Run migrations, seed the bootstrap admin, and start the API:

```bash
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload --port 8000
```

## First-time setup through API

1. Log in as the bootstrap Super Admin:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"ChangeMe-Immediately-123!"}'
```

2. Use the returned `access_token` as a Bearer token. Create a department:

```bash
curl -X POST http://localhost:8000/api/v1/admin/departments \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d '{"code":"LAB-01","name":"Central Quality Lab","location":"Andhra Pradesh"}'
```

3. Register a device. Save `device_secret` securely; it is only returned once:

```bash
curl -X POST http://localhost:8000/api/v1/admin/devices \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d '{"device_id":"RICE-DEVICE-001","serial_number":"RICE-SN-001","department_id":1,"friendly_name":"Rice Lab Kiosk"}'
```

4. Create department users through `POST /api/v1/admin/users` with role `DEPARTMENT_ADMIN` or `DEPARTMENT_USER`. Public self-registration is intentionally disabled.

## Simulated IoT device end-to-end test

Install requirements in the backend environment and run the API first. Then, from the repository root:

```bash
# macOS/Linux
export RICE_AGE_DEVICE_ID=RICE-DEVICE-001
export RICE_AGE_DEVICE_SECRET='DEVICE_SECRET_RETURNED_AT_REGISTRATION'
python backend/scripts/simulate_iot_device.py

# Windows PowerShell
$env:RICE_AGE_DEVICE_ID="RICE-DEVICE-001"
$env:RICE_AGE_DEVICE_SECRET="DEVICE_SECRET_RETURNED_AT_REGISTRATION"
python backend/scripts/simulate_iot_device.py
```

The simulator posts sample JSON, uploads the supplied sample certificate PDF plus two generated PNG test images, and calls finalize. It uses a clearly labeled simulated submission; the sample PDF is included only as a report-format fixture. Do not treat it as proof of device or statutory certification.

## Tests

```bash
cd backend
python -m pytest -q
```

Tests use an isolated in-memory SQLite database and temporary private file storage. They cover end-to-end ingestion, no premature completion, private attachment retrieval, exact retry idempotency, conflicting replay, payload device identity, department isolation, and historical ownership on device reassignment.

For PostgreSQL verification, run `docker compose up -d postgres`, set `DATABASE_URL` to the compose PostgreSQL URL, then run migrations and the tests against that database. This environment does not implicitly claim a PostgreSQL test has passed unless you run it.

## API route summary

| Method | Route | Purpose |
|---|---|---|
| POST | `/api/v1/auth/login` | Human login |
| GET | `/api/v1/auth/me` | Current human identity |
| POST/GET | `/api/v1/admin/departments` | Department create/list |
| POST/GET | `/api/v1/admin/users` | User create/list |
| POST/GET | `/api/v1/admin/devices` | Device register/list |
| POST | `/api/v1/admin/devices/{id}/reassign` | Reassign device |
| POST | `/api/v1/admin/devices/{id}/suspend` | Suspend device |
| POST | `/api/v1/admin/devices/{id}/rotate-credential` | Rotate device secret |
| POST | `/api/v1/device-auth/token` | Device authentication |
| POST | `/api/v1/device/scans` | Submit scan JSON |
| POST | `/api/v1/device/scans/{id}/attachments/prepare` | Get upload manifest/instructions |
| PUT | `/api/v1/device/scans/{id}/attachments/{role}` | Upload one attachment |
| POST | `/api/v1/device/scans/{id}/finalize` | Verify attachments and complete scan |
| GET | `/api/v1/device/scans/{id}/status` | Device submission status |
| GET | `/api/v1/scans/{id}` | Protected scan metadata (authorization boundary test) |
| GET | `/api/v1/scans/{id}/files/{role}` | Protected private file (authorization boundary test) |

## Important assumptions and pending decisions

- **All three attachment roles are required** (`REPORT_PDF`, `BOTTOM_PLATEN`, `TOP_PLATEN`) for this implementation because the requested P2 verification explicitly asks for the original PDF and both images. SOR V5.0 leaves universal attachment requirements for stakeholder confirmation.
- The API preserves device-provided age and verdict fields as received; it does not validate the scientific/quality method. Age units, confidence semantics, rule authority, file limits, offline buffering and hosting remain subject to IoT/product sign-off.
- The sample certificate PDF says “digitally verified” and “official certificate”; project documentation says the sample output is a prototype/advisory artifact and not certification. The application preserves the original file but does not generate or assert certification.
- Local storage is private to the API process and is appropriate for development. For production, configure encrypted private object storage, HTTPS, secret management, backups, malware scanning and retention controls.
