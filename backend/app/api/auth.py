from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from ..config import settings
from ..dependencies import get_current_user, get_db
from ..models import User
from ..schemas import LoginRequest, RegisterRequest, TokenResponse, UserOut
from ..security import create_access_token, hash_password, verify_password
from ..services.activity import record_activity


router = APIRouter(prefix="/auth", tags=["auth"])


def _verify_password_with_pgcrypto(db: Session, password: str, password_hash: str) -> bool:
    """Fallback bcrypt verification using Postgres pgcrypto when python bcrypt isn't installed."""
    if not password_hash.startswith("$2"):
        return False
    try:
        result = db.execute(
            text("SELECT crypt(:password, :stored_hash) = :stored_hash"),
            {"password": password, "stored_hash": password_hash},
        ).scalar()
    except Exception:
        return False
    return bool(result)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    email = payload.email.lower().strip()
    existing = db.scalar(select(User).where(User.email == email))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    make_admin = bool(
        settings.admin_bootstrap_secret
        and payload.admin_secret
        and payload.admin_secret == settings.admin_bootstrap_secret
    )
    user = User(
        name=payload.name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
        is_admin=make_admin,
    )
    db.add(user)
    db.flush()
    record_activity(
        db,
        user_id=user.id,
        activity_type="account_registered",
        details={"is_admin": bool(user.is_admin)},
    )
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=str(user.id), is_admin=user.is_admin)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    email = payload.email.lower().strip()
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    verified = verify_password(payload.password, user.password_hash)
    verified_with_pgcrypto = False
    if not verified:
        verified_with_pgcrypto = _verify_password_with_pgcrypto(db, payload.password, user.password_hash)
        verified = verified_with_pgcrypto

    if not verified:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if verified_with_pgcrypto:
        user.password_hash = hash_password(payload.password)

    record_activity(
        db,
        user_id=user.id,
        activity_type="account_login",
        details={"legacy_hash_migrated": verified_with_pgcrypto},
    )
    db.commit()

    token = create_access_token(subject=str(user.id), is_admin=user.is_admin)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(current_user)
