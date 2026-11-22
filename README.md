# Rice Age — P1/P2 Foundation + P3 Department Portal

Rice Age is a departmental IoT rice quality and age analysis portal. This repository now contains the P1/P2 backend and ingestion foundation plus the P3 user-facing dashboard, scan history, scan details, protected optical image viewer and original PDF preview.

## Scope in this release

### P1 — Foundation
- FastAPI application, PostgreSQL persistence, SQLAlchemy models and Alembic migrations.
- Human login and role-based access for `SUPER_ADMIN`, `DEPARTMENT_ADMIN` and `DEPARTMENT_USER`.
- Department and user administration; device registry and historical department assignment ledger.

### P2 — IoT ingestion
- Device-specific authentication, activation, credential rotation and short-lived machine tokens.
- Versioned JSON scan submission, idempotency, immutable department ownership snapshot and normalized measurement records.
- Private PDF and optical image uploads with file signature, MIME, size and SHA-256 verification.
- Finalization state machine that only marks a scan `Completed` after required attachments are present and re-verified.
- Simulated IoT device client.

### P3 — Department portal
- Sign-in page and authenticated application shell.
- Super Admin overview with department, device and completed/flagged scan counts.
- Department-scoped dashboard with latest completed scan and recent activity.
- Latest scan details: sample/batch/lot, device, grain data, nullable rice age, source verdict and complete quality parameter rows.
- Quality table retains permissible limit, mass-basis %, count-basis %, kernel count, estimated kernel mass and source status as separate fields.
- Grain profile and device-supplied biochemical age/freshness context, including sample uniformity, age breakdown, testing station and color-reference guide when supplied.
- Side-by-side protected bottom/top platen previews with click-to-enlarge image viewer.
- Scan history with server-side pagination and filters for sample, batch, lot, device, verdict, processing state and date range.
- Scan detail page with source evaluation, measurements, verified attachment metadata and original device-generated PDF preview, open, download and print actions.
- All scan read APIs enforce department scope server-side. A non-Super Admin cannot widen scope by supplying another `department_id`.

**Not included yet:** P4 analytics charts and batch comparison; P5 notifications and additional operational hardening; P6 production deployment and acceptance testing. No dashboard feature generates a new quality certificate or alters the uploaded device PDF.

## Prerequisites

- Docker Desktop + Docker Compose plugin
- Windows PowerShell, macOS Terminal or Linux shell
- Internet access during the first Docker build to download base images and frontend/backend dependencies

## Run with Docker Compose (recommended)

From the repository root:

```powershell
Copy-Item .env.example .env
```

Edit `.env`. Set a unique `SECRET_KEY`, strong bootstrap admin password, and a URL-safe PostgreSQL password. The `POSTGRES_PASSWORD` value must match the database password used by Compose. For production, use proper secret management rather than committing `.env`.

Build and start PostgreSQL, FastAPI and the React/Vite frontend:

```powershell
docker compose up --build -d
```

Check service status:

```powershell
docker compose ps
```

Expected services:
- `postgres`: healthy
- `api`: running on `http://localhost:8000`
- `frontend`: running on `http://localhost:5173`

Open:
- Portal: `http://localhost:5173`
- API documentation: `http://localhost:8000/docs`
- API health: `http://localhost:8000/health`

The frontend proxies `/api` requests to the FastAPI container, so browser API calls do not need a separate CORS setup in local Compose development.

### Existing P1/P2 users upgrading to P3

Keep your existing PostgreSQL volume and `.env`. From the updated repository root run:

```powershell
docker compose up --build -d api frontend
```

No database schema migration is required for P3; this phase adds read APIs and frontend files only. Do **not** run `docker compose down -v`, because `-v` deletes the PostgreSQL data volume.

If the frontend fails to build, inspect its logs:

```powershell
docker compose logs --tail 100 frontend
```

API logs:

```powershell
docker compose logs --tail 100 api
```

Stop services without deleting data:

```powershell
docker compose down
```

## First login

Use the `BOOTSTRAP_ADMIN_EMAIL` and `BOOTSTRAP_ADMIN_PASSWORD` values configured in `.env`. The backend creates the bootstrap Super Admin once if it does not already exist. Changing the `.env` bootstrap password later does not automatically update an existing account; use a deliberate password reset procedure.

Sign in at `http://localhost:5173`.

Create departments and devices through the Administration endpoints in Swagger (`http://localhost:8000/docs`). The portal currently provides dashboard/scan read workflows; administration management UI is not part of P3.

## Simulated scan for the full P3 report view

The updated simulator creates `SIM-SCAN-0038-FULL` by default, using the supplied Sample-0038 report data with all nine source quality parameters, grain profile fields and biochemical age/freshness context. It also uploads the supplied original PDF and two generated test PNG placeholders. These generated images are test fixtures, not actual scanner captures. The new client scan ID avoids changing the earlier immutable `SIM-SCAN-0038` submission. Re-running the same simulator ID is an idempotent replay and does not create another scan row.

Example simulator command (run only if the device secret is available):

```powershell
$env:RICE_AGE_DEVICE_ID="RICE-DEVICE-001"
$env:RICE_AGE_DEVICE_SECRET="YOUR_DEVICE_SECRET"
docker compose exec -e "RICE_AGE_DEVICE_ID=$env:RICE_AGE_DEVICE_ID" -e "RICE_AGE_DEVICE_SECRET=$env:RICE_AGE_DEVICE_SECRET" api python /app/scripts/simulate_iot_device.py --pdf /app/docs/reference/APSCSCL_Quality_Certificate_Sample-0038.pdf
```

## Tests

Backend tests run against an isolated SQLite database and temporary private file storage:

```powershell
docker compose exec api python -m pytest -q
```

Or run from `backend/` in a Python environment with `backend/requirements.txt` installed:

```powershell
python -m pytest -q
```

P3 API tests cover department-scoped dashboard summary, latest completed scan behavior, full nine-row scan detail serialization, age/freshness metadata, history filters, rejection of department-scope widening by departmental users, and rejection of unverified file retrieval.

## Frontend local development without Docker

Install Node.js 22+, then:

```powershell
cd frontend
npm install
$env:VITE_PROXY_TARGET="http://127.0.0.1:8000"
npm run dev
```

Open `http://localhost:5173`. Build the frontend with:

```powershell
npm run build
```

## P3 API endpoints

| Method | Route | Purpose |
|---|---|---|
| GET | `/api/v1/dashboard/summary` | Role-scoped dashboard summary, recent scans and latest completed scan |
| GET | `/api/v1/scans/latest` | Latest completed scan within authorized department scope |
| GET | `/api/v1/scans` | Server-side paginated scan history with filters |
| GET | `/api/v1/scans/{scan_id}` | Authorized scan details, quality rows, age output, measurements and attachment metadata |
| GET | `/api/v1/scans/{scan_id}/files/{role}` | Authenticated inline access to original PDF or optical image |

Existing P1/P2 routes are documented in the SOR and Swagger UI.

## Data and certification safeguards

- Processing status and quality verdict are displayed separately.
- `PASS`, `FLAG`, age values and measurement values are source/device reported; the portal does not invent or silently recalculate them.
- Mass-basis and count-basis percentages are displayed independently and are never blended into a single value.
- Missing age results display as unavailable.
- Original PDF bytes are served from private storage; the portal does not recreate or modify the source certificate.
- A sample PDF's visual wording (including digital verification/certificate wording) is not independently validated by this portal. Prototype/advisory disclaimers remain important until the authorized quality authority confirms the rules and certification basis.
- File retrieval uses a human access token, backend department ownership checks and verified-attachment checks, not public file URLs.

## Remaining decisions / limits

- Confirm final age-output semantics and method/version with the IoT team.
- Confirm authoritative quality rules and resolve any sample UI/PDF verdict discrepancies.
- Confirm whether the three attachment roles are mandatory for every future hardware configuration.
- Configure production object storage, HTTPS, secrets management, backups, retention and monitoring before deployment.
- No physical scanner firmware was tested in this workspace; P2 was exercised with a simulator.
