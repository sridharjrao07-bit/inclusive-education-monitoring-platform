"""
Authentication & Authorization — JWT tokens, password hashing, RBAC dependencies.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os

from database import get_db
from models import User

load_dotenv()

# ─── Configuration ───────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# ─── Password Hashing (bcrypt) ──────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ─── OAuth2 scheme (reads token from Authorization header) ─
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ═══════════════════════════════════════════════════════════
# Utility Functions
# ═══════════════════════════════════════════════════════════
def hash_password(plain: str) -> str:
    """Hash a plaintext password with bcrypt."""
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against its bcrypt hash."""
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT token with the given payload and expiry."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ═══════════════════════════════════════════════════════════
# FastAPI Dependencies — Current User
# ═══════════════════════════════════════════════════════════
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Decode JWT token, look up the user in the database, and return the User object.
    Raises 401 if the token is invalid or the user doesn't exist.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


# Helper to allow unauthenticated access (public endpoints)
def get_optional_user(
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Return user if token is valid, else None (allows public access)."""
    if token is None:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        user = db.query(User).filter(User.username == username).first()
        return user if user and user.is_active else None
    except JWTError:
        return None


# ═══════════════════════════════════════════════════════════
# RBAC Dependencies — Three-tier roles
#   national_admin  → full access to all data
#   state_admin     → access filtered to their state
#   teacher         → access filtered to their school
# ═══════════════════════════════════════════════════════════
ADMIN_ROLES = ("national_admin", "state_admin", "admin")  # "admin" kept for backward compat


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Allow national_admin, state_admin, or legacy admin."""
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


def require_national_admin(current_user: User = Depends(get_current_user)) -> User:
    """Only allow national_admin (or legacy admin)."""
    if current_user.role not in ("national_admin", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="National admin access required",
        )
    return current_user


def require_teacher_or_admin(current_user: User = Depends(get_current_user)) -> User:
    """Allow admin, teacher, and student roles."""
    allowed = ("national_admin", "state_admin", "admin", "teacher", "student")
    if current_user.role not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return current_user


def require_own_school(school_id: int, current_user: User = Depends(get_current_user)) -> User:
    """
    Teachers can only access resources from their own school.
    Admins can access any school (state_admin limited by state elsewhere).
    """
    if current_user.role in ADMIN_ROLES:
        return current_user
    if current_user.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access resources from your own school",
        )
    return current_user
