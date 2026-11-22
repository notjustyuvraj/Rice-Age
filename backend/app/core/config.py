from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(ROOT_DIR / ".env", ROOT_DIR / "backend" / ".env"), extra="ignore")
    app_name: str = "Rice Age API"
    environment: str = "development"
    database_url: str = "sqlite:///./rice_age_dev.db"
    secret_key: str = "development-only-change-this-secret-key-32-chars"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    device_token_minutes: int = 15
    storage_root: Path = ROOT_DIR / "storage"
    max_upload_bytes: int = 15 * 1024 * 1024
    cors_origins: str = "http://localhost:5173"
    bootstrap_admin_email: str = "admin@riceage.local"
    bootstrap_admin_password: str = "ChangeMe-Immediately-123!"
    require_all_attachments: bool = True

    @property
    def allowed_origins(self) -> list[str]:
        return [v.strip() for v in self.cors_origins.split(",") if v.strip()]

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
