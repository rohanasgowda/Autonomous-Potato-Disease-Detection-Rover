from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.db.session import Base, engine
from app.models import User  # noqa: F401 - imports register metadata


def create_database() -> None:
    Base.metadata.create_all(bind=engine)


def seed_default_users(db: Session) -> None:
    settings = get_settings()
    defaults = [
        (
            settings.DEFAULT_ADMIN_USERNAME,
            settings.DEFAULT_ADMIN_PASSWORD,
            "admin",
        ),
        (
            settings.DEFAULT_VENDOR_USERNAME,
            settings.DEFAULT_VENDOR_PASSWORD,
            "vendor",
        ),
    ]

    for username, password, role in defaults:
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            continue
        db.add(
            User(
                username=username,
                password_hash=get_password_hash(password),
                role=role,
            )
        )
    db.commit()
