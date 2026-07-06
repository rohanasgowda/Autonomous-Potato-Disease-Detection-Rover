from functools import lru_cache
import os


class Settings:
    PROJECT_NAME = "Plant Disease Detection Rover Backend"
    API_VERSION = "0.1.0"

    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./plant_rover.db")
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-development-secret")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

    DEFAULT_ADMIN_USERNAME = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
    DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")
    DEFAULT_VENDOR_USERNAME = os.getenv("DEFAULT_VENDOR_USERNAME", "vendor")
    DEFAULT_VENDOR_PASSWORD = os.getenv("DEFAULT_VENDOR_PASSWORD", "vendor123")

    DEFAULT_VENDOR_ID = os.getenv("DEFAULT_VENDOR_ID", "vendor_001")
    CURRENCY = os.getenv("CURRENCY", "INR")
    LOW_STOCK_THRESHOLD_KG = float(os.getenv("LOW_STOCK_THRESHOLD_KG", "1.0"))
    FRONTEND_CORS_ORIGINS = os.getenv(
        "FRONTEND_CORS_ORIGINS",
        "http://localhost:5500,http://127.0.0.1:5500,http://localhost:8001,http://127.0.0.1:8001,http://localhost:8080,http://127.0.0.1:8080",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
