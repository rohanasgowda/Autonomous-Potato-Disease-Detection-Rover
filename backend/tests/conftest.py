from collections.abc import Generator
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.security import get_password_hash
from app.db.session import Base, get_db
from app.main import create_app
from app.models.user import User


@pytest.fixture()
def client(tmp_path) -> Generator[TestClient, None, None]:
    database_path = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{database_path}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    testing_session_local = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        future=True,
    )
    Base.metadata.create_all(bind=engine)

    db = testing_session_local()
    db.add_all(
        [
            User(username="admin", password_hash=get_password_hash("admin123"), role="admin"),
            User(username="vendor", password_hash=get_password_hash("vendor123"), role="vendor"),
            User(username="viewer", password_hash=get_password_hash("viewer123"), role="viewer"),
        ]
    )
    db.commit()
    db.close()

    app = create_app(init_database=False)

    def override_get_db() -> Generator[Session, None, None]:
        session = testing_session_local()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def admin_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def viewer_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/auth/login",
        json={"username": "viewer", "password": "viewer123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def sample_detection_payload() -> dict:
    return {
        "session_id": "sess_20260523_001",
        "device_id": "rpi_rover_01",
        "timestamp": "2026-05-23T10:30:00+05:30",
        "grid_position": {"row_index": 1, "plant_index": 7},
        "crop": "potato",
        "disease": "late_blight",
        "confidence": 0.92,
        "severity": {
            "label": "moderate",
            "infected_area_percent": 14.6,
            "method": "leaf_area_segmentation_v1",
        },
        "image": {
            "local_path": "captures/sess_20260523_001.jpg",
            "width": 1280,
            "height": 720,
        },
        "model": {
            "name": "plant_disease_mobilenetv3",
            "version": "0.1.0",
            "runtime": "tflite",
        },
    }


@pytest.fixture()
def future_expiry_date() -> str:
    return date(2027, 2, 15).isoformat()
