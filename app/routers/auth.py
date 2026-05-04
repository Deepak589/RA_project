from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.dependencies import require_current_user, require_current_user_id
from app.core.security import create_access_token, create_refresh_token, hash_password, hash_token, verify_password
from app.db.session import get_db_session
from app.models.user import AuthenticationSession, User, UserPreferences
from app.schemas.user import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
    UserUpdateRequest,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

COOKIE_NAME = "ra_refresh"
COOKIE_OPTIONS = dict(
    httponly=True,
    secure=False,
    samesite="lax",
    max_age=60 * 60 * 24 * 30,
    path="/",
)


async def _load_user(db: AsyncSession, user_id: UUID) -> User | None:
    return await db.scalar(
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.preferences), selectinload(User.medications))
    )


async def _issue_tokens(db: AsyncSession, user: User, old_session: AuthenticationSession | None = None) -> TokenResponse:
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if old_session is not None:
        old_session.revoked_at = now
        old_session.last_used_at = now
    db.add(
        AuthenticationSession(
            user_id=user.id,
            refresh_token_hash=hash_token(refresh_token),
            issued_at=now,
            expires_at=now + timedelta(days=settings.refresh_token_expire_days),
        )
    )
    await db.commit()
    loaded = await _load_user(db, user.id)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, user=loaded or user)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    existing = await db.scalar(select(User).where(User.email.ilike(data.email)))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "EMAIL_ALREADY_EXISTS",
                "message": "An account with this email already exists.",
            },
        )
    if len(data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "PASSWORD_TOO_SHORT",
                "message": "Password must be at least 8 characters.",
            },
        )
    user = User(email=data.email.lower(), full_name=data.name, timezone=data.timezone, password_hash=hash_password(data.password))
    db.add(user)
    await db.flush()
    db.add(UserPreferences(user_id=user.id))
    tokens = await _issue_tokens(db, user)
    response.set_cookie(key=COOKIE_NAME, value=tokens.refresh_token, **COOKIE_OPTIONS)
    return tokens


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    user = await db.scalar(select(User).where(User.email.ilike(data.email)))
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    user.last_login_at = datetime.now(timezone.utc).replace(tzinfo=None)
    tokens = await _issue_tokens(db, user)
    response.set_cookie(key=COOKIE_NAME, value=tokens.refresh_token, **COOKIE_OPTIONS)
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    response: Response,
    data: RefreshRequest | None = Body(default=None),
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    from app.core.security import decode_token

    refresh_token = request.cookies.get(COOKIE_NAME) or (data.refresh_token if data is not None else None)
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is required")

    try:
        payload = decode_token(refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token") from exc
    if payload.get("type") != "refresh" or not payload.get("sub"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    session = await db.scalar(
        select(AuthenticationSession).where(
            AuthenticationSession.refresh_token_hash == hash_token(refresh_token),
            AuthenticationSession.revoked_at.is_(None),
            AuthenticationSession.expires_at > datetime.now(timezone.utc).replace(tzinfo=None),
        )
    )
    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is no longer valid")
    user = await _load_user(db, UUID(str(payload["sub"])))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    tokens = await _issue_tokens(db, user, old_session=session)
    response.set_cookie(key=COOKIE_NAME, value=tokens.refresh_token, **COOKIE_OPTIONS)
    return tokens


@router.post("/logout")
async def logout(
    response: Response,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(require_current_user_id),
) -> dict[str, str]:
    result = await db.scalars(
        select(AuthenticationSession).where(
            AuthenticationSession.user_id == UUID(user_id),
            AuthenticationSession.revoked_at.is_(None),
        )
    )
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    for session in result:
        session.revoked_at = now
    await db.commit()
    response.delete_cookie(key=COOKIE_NAME, path="/")
    return {"status": "logged_out"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(require_current_user)) -> User:
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_me(
    data: UserUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_current_user),
) -> User:
    if data.name is not None:
        current_user.full_name = data.name
    current_user.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.commit()
    loaded = await _load_user(db, current_user.id)
    return loaded or current_user


@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_current_user),
) -> dict[str, str]:
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect")
    current_user.password_hash = hash_password(data.new_password)
    result = await db.scalars(select(AuthenticationSession).where(AuthenticationSession.user_id == current_user.id))
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    for session in result:
        session.revoked_at = now
    await db.commit()
    return {"status": "password_changed"}
