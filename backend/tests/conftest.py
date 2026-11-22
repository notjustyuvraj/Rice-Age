import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.database import Base, get_db
from app.main import app
from app.core.security import hash_secret
from app.models import User
from app.core.config import settings

@pytest.fixture()
def client(tmp_path, monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(engine)
    app.state.test_session_factory = TestingSession
    db = TestingSession()
    db.add(User(email="root@example.com", full_name="Test Super Admin", password_hash=hash_secret("Root-Passphrase-123!"), role="SUPER_ADMIN", department_id=None))
    db.commit(); db.close()
    def override_get_db():
        session = TestingSession()
        try: yield session
        finally: session.close()
    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(settings, "storage_root", tmp_path / "private-storage")
    settings.storage_root.mkdir(parents=True, exist_ok=True)
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    if hasattr(app.state, "test_session_factory"): del app.state.test_session_factory
    Base.metadata.drop_all(engine)
    engine.dispose()

@pytest.fixture()
def admin_headers(client):
    response = client.post("/api/v1/auth/login", json={"email":"root@example.com", "password":"Root-Passphrase-123!"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}

@pytest.fixture()
def registered_device(client, admin_headers):
    dept = client.post("/api/v1/admin/departments", headers=admin_headers, json={"code":"DEPT-A", "name":"Department A"})
    assert dept.status_code == 201, dept.text
    result = client.post("/api/v1/admin/devices", headers=admin_headers, json={"device_id":"RICE-DEVICE-001", "serial_number":"SERIAL-001", "department_id":dept.json()["id"], "friendly_name":"Lab Kiosk"})
    assert result.status_code == 201, result.text
    assert result.json()["device"]["status"] == "PENDING_ENROLLMENT"
    token = client.post("/api/v1/device-auth/token", json={"device_id":"RICE-DEVICE-001", "device_secret":result.json()["device_secret"]})
    assert token.status_code == 200, token.text
    identity = client.get("/api/v1/device-auth/identity", headers={"Authorization":f"Bearer {token.json()['access_token']}"})
    assert identity.status_code == 200 and identity.json()["status"] == "ACTIVE"
    return {"department_id":dept.json()["id"], "device_id":"RICE-DEVICE-001", "headers":{"Authorization":f"Bearer {token.json()['access_token']}"}}
