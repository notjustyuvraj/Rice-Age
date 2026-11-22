import hashlib, os, uuid
from io import BytesIO
from PIL import Image, UnidentifiedImageError
from pathlib import Path
from fastapi import HTTPException, UploadFile
from app.core.config import settings

Image.MAX_IMAGE_PIXELS = 25_000_000

ROLE_TYPES = {
    "REPORT_PDF": {"application/pdf"},
    "BOTTOM_PLATEN": {"image/jpeg", "image/png"},
    "TOP_PLATEN": {"image/jpeg", "image/png"},
}

def validate_signature(role: str, content: bytes, content_type: str | None = None) -> bool:
    if role == "REPORT_PDF": return content.startswith(b"%PDF-")
    if role in ("BOTTOM_PLATEN", "TOP_PLATEN"):
        if not (content.startswith(b"\x89PNG\r\n\x1a\n") or content.startswith(b"\xff\xd8\xff")):
            return False
        try:
            with Image.open(BytesIO(content)) as image:
                image_format = image.format
                image.verify()
            expected = {"image/png": "PNG", "image/jpeg": "JPEG"}.get(content_type)
            return expected is None or image_format == expected
        except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
            return False
    return False

async def store_upload(upload: UploadFile, role: str) -> tuple[str, str, int, str]:
    if role not in ROLE_TYPES: raise HTTPException(422, "Unsupported attachment role")
    content_type = (upload.content_type or "").lower()
    if content_type not in ROLE_TYPES[role]: raise HTTPException(415, f"Invalid content type for {role}")
    data = await upload.read(settings.max_upload_bytes + 1)
    if not data: raise HTTPException(400, "Empty attachment")
    if len(data) > settings.max_upload_bytes: raise HTTPException(413, "Attachment exceeds configured size limit")
    if not validate_signature(role, data, content_type): raise HTTPException(415, "Attachment content does not match its declared type")
    digest = hashlib.sha256(data).hexdigest()
    key = f"{uuid.uuid4().hex[:2]}/{uuid.uuid4().hex}"
    root: Path = settings.storage_root.resolve()
    destination = (root / key).resolve()
    if root not in destination.parents: raise HTTPException(400, "Invalid storage key")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = destination.with_suffix(".part")
    try:
        with open(temp, "xb") as f:
            f.write(data); f.flush(); os.fsync(f.fileno())
        os.replace(temp, destination)
    finally:
        if temp.exists(): temp.unlink()
    return key, content_type, len(data), digest

def resolve_storage_key(key: str) -> Path:
    root = settings.storage_root.resolve()
    path = (root / key).resolve()
    if root not in path.parents or not path.is_file(): raise FileNotFoundError(key)
    return path
