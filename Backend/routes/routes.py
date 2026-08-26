from flask import request

from services.user_services import create_user, login_user
from services.questionAPI import get_response


def register_routes(app):

    @app.route("/")
    def home():
        return {
            "message": "Backend is running"
        }

    # -------------------------
    # CREATE NEW USER
    # -------------------------

    @app.route("/NewUser_login", methods=["POST"])
    def receive_NewUser_data():

        NewUserdata = request.get_json(silent=True) or {}

        if not isinstance(NewUserdata, dict):
            return {
                "error": "Invalid JSON payload"
            }, 400

        required_fields = {
            "Username",
            "NewPassword"
        }

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

        if (
            not isinstance(local_username, str)
            or not isinstance(local_password, str)
        ):
            return {
                "error": "Username and NewPassword must both be strings"
            }, 400

        # Call service
        user, error = create_user(
            local_username,
            local_password
        )

        if error == "Username already exists":
            return {
                "error": error
            }, 409

        if error == "Database query failed":
            return {
                "error": error
            }, 500

        if error == "Failed to create user":
            return {
                "error": error
            }, 500

        return {
            "message": "User created successfully",
            "data": {
                "id": user.id,
                "username": user.username,
            },
        }, 201


    # -------------------------
    # LOGIN EXISTING USER
    # -------------------------

    @app.route("/Old_User_login", methods=["POST"])
    def receive_OldUser_data():

        Userdata = request.get_json(silent=True) or {}

        if not isinstance(Userdata, dict):
            return {
                "error": "Invalid JSON payload"
            }, 400

        required_fields = {
            "Username",
            "Password"
        }

        missing_fields = required_fields - Userdata.keys()

        if missing_fields:
            return {
                "error": f"Missing fields: {sorted(missing_fields)}"
            }, 400

        local_username = Userdata.get("Username")
        local_password = Userdata.get("Password")

        if (
            not isinstance(local_username, str)
            or not isinstance(local_password, str)
        ):
            return {
                "error": "Username and Password must both be strings"
            }, 400

        # Call service
        user, error = login_user(
            local_username,
            local_password
        )

        if error == "Database query failed":
            return {
                "error": error
            }, 500

        if error == "Username not found":
            return {
                "error": error
            }, 404

        if error == "Incorrect password":
            return {
                "error": error
            }, 401

        return {
            "message": "Login successful",
            "data": {
                "id": user.id,
                "username": user.username,
            },
        }, 200
        
    @app.route("/QuestionPost", methods=["POST"])
    def receive_Question_data():
        
        question_data = request.get_json(silent=True) or {}
        
        if not isinstance(question_data, dict):
            return {
                "error": "Invalid JSON payload"
            }, 400
            
        required_fields = {
                    "Username",
                    "Question",
                    "Image_path"
                }
        
        missing_fields = required_fields - question_data.keys()
        
        if missing_fields:
            return {
                "error": f"Missing fields: {sorted(missing_fields)}"
            }, 400
            
        username = question_data.get("Username")
        question = question_data.get("Question")
        img_path = question_data.get("Image_path")
        
        try: 
            response = get_response(
                username,
                question,
                img_path
            )
        except Exception as e:
            return {
                "error": f"Failed to get response from Gemini API: {e}"
            }, 500
            
        return response, 200