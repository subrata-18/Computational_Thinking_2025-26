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

def add_UserQuestion(username, question_text, question_img, ai_questions, ai_answers):
    from database.models import Question

    # Create a new Question instance
    new_question = Question(
        username=username,
        question_text=question_text,
        question_img=question_img,
        ai_questions=ai_questions,
        ai_answers=ai_answers
    )

    try:
        db.session.add(new_question)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return None, f"Failed to add question: {e}"

    return ()