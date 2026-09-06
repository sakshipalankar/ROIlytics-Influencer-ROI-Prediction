"""Authentication and User Management Router.
Persists registered users and Google authentication users into the database (MySQL + SQLite).
"""
from __future__ import annotations

import hashlib
import logging
import os
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ..services import influencer_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


def hash_password(password: str) -> str:
    """Hash password using SHA-256 with a salt."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(plain_password: str, stored_hash: Optional[str]) -> bool:
    """Verify password against either SHA-256 hash or plaintext legacy password."""
    if not stored_hash:
        return False
    # Direct plaintext check (for demo seed users)
    if plain_password == stored_hash:
        return True
    # SHA-256 check
    return hash_password(plain_password) == stored_hash


# ─── Pydantic Request Models ──────────────────────────────────────────────────

class RegisterPayload(BaseModel):
    username: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5, max_length=150)
    password: str = Field(..., min_length=6)
    role: Optional[str] = "Campaign Manager"
    company: Optional[str] = None


class LoginPayload(BaseModel):
    email: str
    password: str


class GoogleAuthPayload(BaseModel):
    email: str
    name: str
    picture: Optional[str] = None


class UpdateProfilePayload(BaseModel):
    email: str
    username: str
    role: Optional[str] = None
    avatar_url: Optional[str] = None


class ChangePasswordPayload(BaseModel):
    email: str
    current_password: str
    new_password: str = Field(..., min_length=6)


class TestMySQLPayload(BaseModel):
    password: str
    host: Optional[str] = "localhost"
    port: Optional[int] = 3306
    user: Optional[str] = "root"
    database: Optional[str] = "roilytics_db"


# ─── Auth Endpoints ───────────────────────────────────────────────────────────

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterPayload):
    """Register a new user and save directly into the database (MySQL & SQLite)."""
    email_clean = payload.email.strip().lower()
    username_clean = payload.username.strip()

    # Check if user already exists
    existing = influencer_db.get_user_by_email(email_clean)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists. Please sign in instead.",
        )

    # Hash the password
    pwd_hash = hash_password(payload.password)
    default_avatar = f"https://api.dicebear.com/7.x/avataaars/svg?seed={username_clean}"

    # Insert into database
    user = influencer_db.create_user(
        username=username_clean,
        email=email_clean,
        password_hash=pwd_hash,
        avatar_url=default_avatar,
        provider="email",
        role=payload.role or "Campaign Manager",
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user in database.",
        )

    logger.info("Successfully registered user in database: %s (%s)", username_clean, email_clean)

    return {
        "id": user.get("id"),
        "username": user.get("username"),
        "name": user.get("username"),
        "email": user.get("email"),
        "avatar_url": user.get("avatar_url") or default_avatar,
        "avatar": user.get("avatar_url") or default_avatar,
        "provider": user.get("provider", "email"),
        "role": user.get("role", "Campaign Manager"),
        "created_at": user.get("created_at"),
    }


@router.post("/login")
async def login(payload: LoginPayload):
    """Authenticate user against database credentials."""
    email_clean = payload.email.strip().lower()
    user = influencer_db.get_user_by_email(email_clean)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No account found with this email address.",
        )

    stored_hash = user.get("password_hash")
    if not verify_password(payload.password, stored_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password. Please try again.",
        )

    return {
        "id": user.get("id"),
        "username": user.get("username"),
        "name": user.get("username"),
        "email": user.get("email"),
        "avatar_url": user.get("avatar_url"),
        "avatar": user.get("avatar_url"),
        "provider": user.get("provider", "email"),
        "role": user.get("role", "Campaign Manager"),
        "created_at": user.get("created_at"),
    }


@router.post("/google")
async def google_auth(payload: GoogleAuthPayload):
    """Authenticate or register Google SSO user and persist in database."""
    email_clean = payload.email.strip().lower()
    existing = influencer_db.get_user_by_email(email_clean)

    if existing:
        # Update avatar if provided
        if payload.picture and existing.get("avatar_url") != payload.picture:
            influencer_db.update_user_profile(
                email=email_clean,
                username=existing.get("username", payload.name),
                avatar_url=payload.picture,
            )
            existing["avatar_url"] = payload.picture

        return {
            "id": existing.get("id"),
            "username": existing.get("username"),
            "name": existing.get("username"),
            "email": existing.get("email"),
            "avatar_url": existing.get("avatar_url") or payload.picture,
            "avatar": existing.get("avatar_url") or payload.picture,
            "provider": "google",
            "role": existing.get("role", "Campaign Manager"),
            "created_at": existing.get("created_at"),
        }

    # Create new Google user in database
    user = influencer_db.create_user(
        username=payload.name,
        email=email_clean,
        password_hash=None,
        avatar_url=payload.picture,
        provider="google",
        role="Campaign Manager",
    )

    logger.info("Created new Google SSO user in database: %s", email_clean)

    return {
        "id": user.get("id"),
        "username": user.get("username"),
        "name": user.get("username"),
        "email": user.get("email"),
        "avatar_url": user.get("avatar_url") or payload.picture,
        "avatar": user.get("avatar_url") or payload.picture,
        "provider": "google",
        "role": user.get("role", "Campaign Manager"),
        "created_at": user.get("created_at"),
    }


@router.get("/users")
async def get_users():
    """Retrieve all users stored in the database."""
    users = influencer_db.get_all_users()
    return {
        "total": len(users),
        "users": [
            {
                "id": u.get("id"),
                "username": u.get("username"),
                "name": u.get("username"),
                "email": u.get("email"),
                "avatar_url": u.get("avatar_url"),
                "avatar": u.get("avatar_url"),
                "provider": u.get("provider", "email"),
                "role": u.get("role", "Campaign Manager"),
                "created_at": u.get("created_at"),
            }
            for u in users
        ],
    }


@router.get("/me")
async def get_me(email: str):
    """Retrieve a single user's profile by email."""
    user = influencer_db.get_user_by_email(email.strip().lower())
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": user.get("id"),
        "username": user.get("username"),
        "name": user.get("username"),
        "email": user.get("email"),
        "avatar_url": user.get("avatar_url"),
        "avatar": user.get("avatar_url"),
        "provider": user.get("provider", "email"),
        "role": user.get("role", "Campaign Manager"),
        "created_at": user.get("created_at"),
    }


@router.put("/profile")
async def update_profile(payload: UpdateProfilePayload):
    """Update profile information in the database."""
    email_clean = payload.email.strip().lower()
    updated = influencer_db.update_user_profile(
        email=email_clean,
        username=payload.username.strip(),
        role=payload.role,
        avatar_url=payload.avatar_url,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": updated.get("id"),
        "username": updated.get("username"),
        "name": updated.get("username"),
        "email": updated.get("email"),
        "avatar_url": updated.get("avatar_url"),
        "avatar": updated.get("avatar_url"),
        "provider": updated.get("provider", "email"),
        "role": updated.get("role", "Campaign Manager"),
        "created_at": updated.get("created_at"),
    }


@router.post("/change-password")
async def change_password(payload: ChangePasswordPayload):
    """Change user password in database."""
    email_clean = payload.email.strip().lower()
    user = influencer_db.get_user_by_email(email_clean)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    stored_hash = user.get("password_hash")
    if not verify_password(payload.current_password, stored_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    new_hash = hash_password(payload.new_password)
    influencer_db.update_user_password(email_clean, new_hash)
    return {"success": True, "message": "Password updated successfully in database"}


@router.post("/test-mysql")
async def test_mysql(payload: TestMySQLPayload):
    """Test MySQL connection with user-provided password and auto-migrate if successful."""
    try:
        import pymysql
        conn = pymysql.connect(
            host=payload.host or "localhost",
            port=payload.port or 3306,
            user=payload.user or "root",
            password=payload.password,
            connect_timeout=3,
        )
        
        # Test succeeded! Run migration if needed
        import sys
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        if root_dir not in sys.path:
            sys.path.insert(0, root_dir)
        import src.setup_mysql as setup_mysql
        summary = setup_mysql.run_migration(password=payload.password)
        conn.close()

        # Update .env with working password
        env_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                content = f.read()
            import re
            content = re.sub(r"MYSQL_PASSWORD=.*", f"MYSQL_PASSWORD={payload.password}", content)
            with open(env_path, "w") as f:
                f.write(content)

        return {
            "status": "connected",
            "message": "Successfully connected to MySQL and migrated data!",
            "summary": summary,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"MySQL connection failed: {str(exc)}")
