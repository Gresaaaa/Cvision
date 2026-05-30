import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile


class MediaService:
    ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
    ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "image/webp"}

    def save_image(self, upload: UploadFile, upload_dir: str, folder: str) -> str:
        suffix = Path(upload.filename or "").suffix.lower()
        if suffix not in self.ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Only PNG, JPG, JPEG, and WEBP images are allowed")
        if upload.content_type and upload.content_type.lower() not in self.ALLOWED_CONTENT_TYPES:
            raise HTTPException(status_code=400, detail="Unsupported image type")

        filename = f"{uuid4().hex}{suffix}"
        relative_path = Path(folder) / filename
        destination = Path(upload_dir) / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("wb") as buffer:
            shutil.copyfileobj(upload.file, buffer)
        return f"/uploads/{relative_path.as_posix()}"

    def delete_uploaded_file(self, file_url: str | None, upload_dir: str) -> None:
        if not file_url or not file_url.startswith("/uploads/"):
            return
        relative_path = Path(file_url.removeprefix("/uploads/"))
        if ".." in relative_path.parts:
            return
        full_path = Path(upload_dir) / relative_path
        if full_path.exists() and full_path.is_file():
            full_path.unlink()


media_service = MediaService()
