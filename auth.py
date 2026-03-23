"""
OAuth2 + JWT authentication for the admin dashboard.
- Password hashing with bcrypt
- JWT access tokens (HS256)
- FastAPI dependency for protected routes
"""

import os
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

# --- Config ---
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-production-yarmouk-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8-hour session

# --- OAuth2 scheme (token URL matches the login endpoint) ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/admin/api/login")


# --- Pydantic models ---
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: str


class AdminUser(BaseModel):
    id: int
    username: str
    full_name: str
    is_active: bool


# --- Helpers ---
def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


async def authenticate_user(pool, username: str, password: str) -> dict | None:
    """Verify credentials against the admin_users table. Returns row dict or None."""
    async with pool.connection() as conn:
        cur = await conn.execute(
            "SELECT id, username, full_name, is_active, hashed_password FROM admin_users WHERE username = %s",
            (username,),
        )
        row = await cur.fetchone()
    if not row:
        return None
    # row is a tuple: (id, username, full_name, is_active, hashed_password)
    if not verify_password(password, row[4]):
        return None
    if not row[3]:  # is_active
        return None
    return {"id": row[0], "username": row[1], "full_name": row[2], "is_active": row[3]}


async def get_current_admin(token: str = Depends(oauth2_scheme)) -> TokenData:
    """FastAPI dependency — extracts and validates the JWT from the Authorization header."""
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
        return TokenData(username=username)
    except JWTError:
        raise credentials_exception


async def seed_default_admin(pool):
    """Create a default admin user if the table is empty."""
    async with pool.connection() as conn:
        cur = await conn.execute("SELECT COUNT(*) FROM admin_users")
        row = await cur.fetchone()
        if row[0] == 0:
            default_password = os.getenv("ADMIN_DEFAULT_PASSWORD", "admin123")
            await conn.execute(
                "INSERT INTO admin_users (username, hashed_password, full_name) VALUES (%s, %s, %s)",
                ("admin", hash_password(default_password), "Administrator"),
            )
