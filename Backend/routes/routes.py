from flask import request

from database.db import db
from database.models import User

def register_routes(app):

    @app.route("/")
    def home():
        return {"message": "Backend is running"}

    @app.route("/data", methods=["POST"])
    def receive_data():
        data = request.get_json(silent=True) or {}

        required_fields = {"username", "password", "email_id"}
        allowed_fields = required_fields

        missing_fields = required_fields - data.keys()
        extra_fields = set(data.keys()) - allowed_fields

        if missing_fields:
            return {
                "error": f"Missing fields: {sorted(missing_fields)}"
            }, 400

        if extra_fields:
            return {
                "error": f"Unexpected fields: {sorted(extra_fields)}"
            }, 400

        user = User(
            username=data["username"],
            password=data["password"],
            email_id=data["email_id"],
        )

        db.session.add(user)
        db.session.commit()

        return {
            "message": "User created successfully",
            "data": {
                "id": user.id,
                "username": user.username,
                "email_id": user.email_id,
            },
        }, 201