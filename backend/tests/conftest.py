import os
from pathlib import Path
import shutil

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///./test_cvision.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"
os.environ["OLLAMA_TIMEOUT_SECONDS"] = "2"
os.environ["BOOTSTRAP_ON_STARTUP"] = "true"
os.environ["ADMIN_EMAIL"] = "admin@cvision.io"
os.environ["ADMIN_PASSWORD"] = "Admin123!"
os.environ["UPLOAD_DIR"] = "test_uploads"
Path("test_uploads").mkdir(exist_ok=True)

from app.main import app  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.init_db import seed_base_data  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_base_data(db)
    finally:
        db.close()
    yield
    engine.dispose()
    db_path = Path("test_cvision.db")
    upload_dir = Path("test_uploads")
    if db_path.exists():
        try:
            db_path.unlink()
        except PermissionError:
            pass
    if upload_dir.exists():
        shutil.rmtree(upload_dir, ignore_errors=True)


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client
