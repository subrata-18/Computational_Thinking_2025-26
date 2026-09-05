from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError

from database.db import db
from database.models import User


password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Create a secure Argon2id password hash."""
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against an Argon2id hash."""
    try:
        return password_hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError):
        return False


def create_user(username, password):
    # Check if username already exists
    try:
        existing_user = User.query.filter_by(
            username=username
        ).first()
    except Exception:
        return None, "Database query failed"

    if existing_user:
        return None, "Username already exists"

    # Hash password before storing it
    password_hash = hash_password(password)

    user = User(
        username=username,
        password=password_hash
    )

    try:
        db.session.add(user)
        db.session.commit()

    except Exception:
        db.session.rollback()
        return None, "Failed to create user"

    return user, None


def login_user(username, password):
    # Find user
    try:
        existing_user = User.query.filter_by(
            username=username
        ).first()
    except Exception:
        return None, "Database query failed"

    if not existing_user:
        return None, "Username not found"

    # Verify password against stored Argon2 hash
    if not verify_password(password, existing_user.password):
        return None, "Incorrect password"

    return existing_user, None