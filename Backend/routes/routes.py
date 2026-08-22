from flask import request

from database.db import db
from database.models import User

def register_routes(app):

    @app.route("/")
    def home():
        return {"message": "Backend is running"}

    @app.route("/NewUser_login", methods=["POST"])
    def receive_data():
        NewUserdata = request.get_json(silent=True) or {}

        if not isinstance(NewUserdata, dict):
            return {
                "error": "Invalid JSON payload"
            }, 400

        required_fields = {"Username", "NewPassword"}
        allowed_fields = required_fields

        missing_fields = required_fields - NewUserdata.keys()
        extra_fields = set(NewUserdata.keys()) - allowed_fields

        if missing_fields:
            return {
                "error": f"Missing fields: {sorted(missing_fields)}"
            }, 400

        if extra_fields:
            return {
                "error": f"Unexpected fields: {sorted(extra_fields)}"
            }, 400

        local_username = NewUserdata["Username"]
        local_password = NewUserdata["NewPassword"]

        if not isinstance(local_username, str) or not isinstance(local_password, str):
            return {
                "error": "Username and NewPassword must both be strings"
            }, 400

        try:
            existing_user = User.query.filter_by(username=local_username).first()
        except Exception:
            return {
                "error": "Database query failed"
            }, 500   
            
        if existing_user:
            return {
                "error": "Username already exists"
            }, 409

        user = User(
            username=local_username,
            password=local_password,
        )
        
        try:
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {
                "error": "Failed to create user",
                "exception": str(e)
            }, 500

        return {
            "message": "User created successfully",
            "data": {
                "id": user.id,
                "username": user.username,
            },
        }, 201