import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

# Dummy credentials for testing (no database required)
DUMMY_USERS = {
    "testadmin": {"password": "testadmin123", "role": "admin"},
    "testvendor": {"password": "testvendor123", "role": "vendor"},
    "testviewer": {"password": "testviewer123", "role": "viewer"},
}


@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    # Check if user already exists
    existing_user = db.query(User).filter(User.username == payload.username).first()
    if existing_user:
        logger.warning("Registration failed: username already exists - username=%s", payload.username)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists.",
        )
    
    # Create new user
    new_user = User(
        username=payload.username,
        password_hash=get_password_hash(payload.password),
        role=payload.role,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    logger.info("User registration successful - username=%s role=%s", new_user.username, new_user.role)
    return TokenResponse(
        access_token=create_access_token(subject=new_user.username, role=new_user.role),
        role=new_user.role,
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    # Try database first
    try:
        user = db.query(User).filter(User.username == payload.username).first()
        if user is not None and verify_password(payload.password, user.password_hash):
            logger.info("Authentication succeeded for username=%s role=%s", user.username, user.role)
            return TokenResponse(
                access_token=create_access_token(subject=user.username, role=user.role),
                role=user.role,
            )
    except Exception as e:
        logger.warning("Database error during login: %s", str(e))
    
    # Fallback to dummy credentials for testing
    if payload.username in DUMMY_USERS:
        dummy_user = DUMMY_USERS[payload.username]
        if dummy_user["password"] == payload.password:
            logger.info("Authentication succeeded (dummy) for username=%s role=%s", payload.username, dummy_user["role"])
            return TokenResponse(
                access_token=create_access_token(subject=payload.username, role=dummy_user["role"]),
                role=dummy_user["role"],
            )
    
    logger.warning("Authentication failed for username=%s", payload.username)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid username or password.",
    )
