# Rice Age implementation status

## P1 — Foundation
- FastAPI application, PostgreSQL persistence, SQLAlchemy models and Alembic migration.
- Human login and role-based access for `SUPER_ADMIN`, `DEPARTMENT_ADMIN` and `DEPARTMENT_USER`.
- Department and user administration; device registry and historical department assignment ledger.

## P2 — IoT ingestion
- Device-specific authentication, activation, credential rotation and short-lived machine tokens.
- Versioned JSON scan submission, idempotency, immutable department ownership snapshot and normalized measurement records.
- Private PDF and optical image uploads with file signature, MIME, size and SHA-256 verification.
- Finalization state machine that only marks a scan `Completed` after required attachments are present and re-verified.
- Simulated IoT device fixture using Sample-0038 data.

## P3 — Department portal
- React + Vite + TypeScript + Tailwind application shell and authenticated login.
- Super Admin overview and department-scoped dashboard with scan/device/department counts, latest completed scan and recent activity.
- Server-side paginated scan history with sample, batch, lot, device, quality verdict, processing status and date filters.
- Full scan details: sample and grain profile, nine source quality parameter fields when supplied, independent mass/count bases, kernel counts and estimated kernel mass.
- Device-reported age/freshness context including uniformity, age breakdown, freshness rating, testing station and color-reference guide when supplied; absent age remains unavailable.
- Protected bottom/top platen image previews with click-to-enlarge lightbox.
- Original device PDF preview, open-in-tab, download and print controls; original PDF bytes are preserved.
- Backend file endpoint serves only verified attachments and enforces department ownership.
- Updated simulator creates `SIM-SCAN-0038-FULL` with all nine Sample-0038 quality rows and device-supplied age/freshness fields. Its image files remain explicitly labeled simulation placeholders.

## Verification performed in this workspace
- Backend suite: **9 passed** using isolated SQLite and temporary private storage.
- Python compilation (`compileall`): passed.
- TypeScript/TSX syntax transpilation: **13 files parsed successfully**.

## Not verified in this workspace
- Full frontend TypeScript check/Vite production build: dependencies are not installed in this workspace, and `npm install` timed out while accessing the package registry. Run `docker compose up --build -d api frontend` on the user's machine with registry access, then inspect frontend logs.
- PostgreSQL and browser integration on the user's Windows machine must be rechecked after applying this update.
- Actual scanner platen images and physical hardware integration have not been tested; simulator image placeholders are not real captures.

## Scope boundary
- P4 analytics charts and batch comparison are not implemented.
- P5 notifications are not implemented.
- P6 production deployment/acceptance is not implemented.
