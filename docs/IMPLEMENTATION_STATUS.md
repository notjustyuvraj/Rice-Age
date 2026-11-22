# Rice Age P1/P2 Implementation Status

## Implemented

- P1: FastAPI application structure, SQLAlchemy models, PostgreSQL driver/configuration, Alembic initial migration, human login, scrypt password hashing, three human RBAC roles, departments, department-scoped users, device registry, one-active-department assignment and assignment history.
- P2: device-specific enrollment secret, first-auth activation, short-lived device JWTs, credential rotation/revocation of existing tokens, scan JSON validation, canonical idempotency key, immutable department snapshot, normalized measurement/age/quality records, private attachment storage, MIME/signature/image-decoding/size/SHA-256 checks, upload attempts, finalize state transition, device status, protected scan/file authorization checks, simulated device client.

## Verification performed in this workspace

- `pytest -q`: **5 passed** using isolated in-memory SQLite and temporary private storage.
- `python -m compileall -q app scripts tests`: passed.
- `alembic upgrade head`: passed against a fresh SQLite database.
- `python -m app.seed`: created the bootstrap Super Admin in a fresh SQLite database.
- Live FastAPI smoke test: Super Admin login, department creation, device enrollment/first-auth activation, simulated JSON submission, sample PDF + two valid PNG uploads, and finalization all succeeded. The scan ended in `Completed` with all three attachment roles verified.

## Not verified here / blockers

- This execution environment has no Docker executable, PostgreSQL server or `psql` client. The PostgreSQL driver, Dockerfile and Compose configuration are included, but a real PostgreSQL integration run has **not** been executed here. Run `docker compose up --build -d` and rerun the tests against the Compose database before sign-off.
- No physical IoT firmware/device was available. The end-to-end flow was exercised with the supplied sample certificate PDF and generated test images through the simulator.
- SOR V5.0 leaves attachment requirements, file limits, age-output contract, quality-rule authority and deployment/retention details pending stakeholder sign-off. This implementation requires all three attachment roles because that requirement was explicitly requested for this milestone; it is configurable.
- Upload retry is safe at whole-file request level (same role + same hash is idempotent). Chunked/resumable multipart upload is not implemented.

## Scope boundary

P3 and later are intentionally not implemented: no dashboard/frontend, scan-history UI, analytics UI, Rice Age dashboard, report UI, batch comparison or notifications.
