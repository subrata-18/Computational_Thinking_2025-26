from database.db import db
from database.models import User


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

    # Create user
    user = User(
        username=username,
        password=password
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

    # User doesn't exist
    if not existing_user:
        return None, "Username not found"

    # Check password
    if existing_user.password != password:
        return None, "Incorrect password"

    return existing_user, None

