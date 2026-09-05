import math

from flask import request

from services.user_services import create_user, login_user
from services.admin_services import login_admin, get_admin_user_history, get_admin_history_detail
from services.questionAPI import get_Doubtresponse, get_response
from services.graphical_question import get_graphical_response
from services.score_services import add_ScoreDB
from services.history_services import get_user_history, get_history_detail


def is_valid_coordinates(value):
    if not isinstance(value, list) or len(value) > 4:
        return False

    for point in value:
        if not isinstance(point, list) or len(point) != 2:
            return False
        if not all(isinstance(coordinate, (int, float)) and math.isfinite(coordinate) for coordinate in point):
            return False

    return True


def register_routes(app):

    @app.route("/")
    def home():
        return {
            "message": "Backend is running"
        }
        
    @app.route("/health", methods=["GET"])
    def health():
        return {"status": "ok"}, 200

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

    # -------------------------
    # ADMIN LOGIN
    # -------------------------

    @app.route("/AdminLogin", methods=["POST"])
    def receive_Admin_login_data():
        data = request.get_json(silent=True) or {}
        if not isinstance(data, dict):
            return {"error": "Invalid JSON payload"}, 400

        required_fields = {"Username", "Password"}
        missing_fields = required_fields - data.keys()
        if missing_fields:
            return {"error": f"Missing fields: {sorted(missing_fields)}"}, 400

        username = data.get("Username")
        password = data.get("Password")
        if not isinstance(username, str) or not isinstance(password, str):
            return {"error": "Username and Password must both be strings"}, 400

        admin, error = login_admin(username, password)
        if error == "Username not found":
            return {"error": error}, 404
        if error == "Incorrect password":
            return {"error": error}, 401
        if error:
            return {"error": error}, 500

        return {
            "message": "Admin login successful",
            "data": {"id": admin.id, "username": admin.username},
        }, 200
        
    # -------------------------
    # POST QUESTION
    # -------------------------
        
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
    
    # --------------------------------------
    # For the wrong answered question
    # --------------------------------------
    
    
    @app.route("/DoubtQuestionPost", methods=["POST"])
    def receive_DoubtQuestion_data():
        
        doubt_question_data = request.get_json(silent=True) or {}
        
        if not isinstance(doubt_question_data, dict):
            return {
                "error": "Invalid JSON payload"
            }, 400
            
        required_fields = {
                    "Username",
                    "WrongAnsweredquestion",
                    "QuestionJson"
                }
        
        missing_fields = required_fields - doubt_question_data.keys()
        
        if missing_fields:
            return {
                "error": f"Missing fields: {sorted(missing_fields)}"
            }, 400
            
        username = doubt_question_data.get("Username")
        WrongAnsweredquestion = doubt_question_data.get("WrongAnsweredquestion")
        QuestionJson = doubt_question_data.get("QuestionJson")

        try: 
            response = get_Doubtresponse(
                username,
                WrongAnsweredquestion,
                QuestionJson   
            )
        except Exception as e:
            return {
                "error": f"Failed to get response from Gemini API: {e}"
            }, 500
            
        return response, 200
    
    
    
    
    # --------------------------------------
    # For posting graphical questions
    # --------------------------------------
    
    
    @app.route("/GraphicalQuestionPost", methods=["POST"])
    def receive_GraphicalQuestion_data():
        
        graphical_question_data = request.get_json(silent=True) or {}
        
        if not isinstance(graphical_question_data, dict):
            return {
                "error": "Invalid JSON payload"
            }, 400
            
        required_fields = {
                    "Username",
                    "Question",
                    "Coordinates",
                }
        
        missing_fields = required_fields - graphical_question_data.keys()
        
        if missing_fields:
            return {
                "error": f"Missing fields: {sorted(missing_fields)}"
            }, 400
            
        username = graphical_question_data.get("Username")
        question = graphical_question_data.get("Question")
        coordinates = graphical_question_data.get("Coordinates")


        if not is_valid_coordinates(coordinates):
            return {
                "error": "Coordinates must be an array of up to 4 [x, y] number pairs"
            }, 400
        
        try: 
            response = get_graphical_response(
                username,
                question,
                coordinates
            )
        except Exception as e:
            return {
                "error": f"Failed to get response from Gemini API: {e}"
            }, 500
            
        return response, 200
    
    
    
    # --------------------------------------
    # For getting the Score after the quiz
    # --------------------------------------
    
    @app.route("/ScorePost", methods=["POST"])
    def receive_Score_data():
        
        score_data = request.get_json(silent=True) or {}
        
        if not isinstance(score_data, dict):
            return {
                "error": "Invalid JSON payload"
            }, 400
            
        required_fields = {
                    "Username",
                    "QuestionJson",
                    "wrong_answered_questions",
                    "Score"
                }
        
        missing_fields = required_fields - score_data.keys()
        
        if missing_fields:
            return {
                "error": f"Missing fields: {sorted(missing_fields)}"
            }, 400
            
        username = score_data.get("Username")
        QuestionJson = score_data.get("QuestionJson")
        Score = score_data.get("Score")
        wrong_answered_questions = score_data.get("wrong_answered_questions")
        try:
            add_ScoreDB(
                username,
                QuestionJson,
                wrong_answered_questions,
                Score
            )
        except Exception as e:
            return {
                "error": f"Failed to add score entry: {e}"
            }, 500
        
        return {
            "message": "Score entry added successfully"
        }, 200

        
    # -------------------------
    # GET USER CHAT HISTORY
    # -------------------------
    
    @app.route("/GetUserHistory", methods=["POST"])
    def get_user_history_data():
        
        history_request = request.get_json(silent=True) or {}
        
        if not isinstance(history_request, dict):
            return {
                "error": "Invalid JSON payload"
            }, 400
            
        required_fields = {"Username"}
        
        missing_fields = required_fields - history_request.keys()
        
        if missing_fields:
            return {
                "error": f"Missing fields: {sorted(missing_fields)}"
            }, 400
            
        username = history_request.get("Username")
        
        if not isinstance(username, str):
            return {
                "error": "Username must be a string"
            }, 400
        
        try:
            history_data, error = get_user_history(username)
            
            if error:
                return {
                    "error": error
                }, 500
            
            return {
                "message": "History retrieved successfully",
                "data": history_data
            }, 200
        except Exception as e:
            return {
                "error": f"Failed to retrieve history: {e}"
            }, 500


    # -------------------------
    # GET HISTORY DETAIL
    # -------------------------
    
    @app.route("/GetHistoryDetail", methods=["POST"])
    def get_history_detail_data():
        
        history_detail_request = request.get_json(silent=True) or {}
        
        if not isinstance(history_detail_request, dict):
            return {
                "error": "Invalid JSON payload"
            }, 400
            
        required_fields = {"Username", "HistoryId"}
        
        missing_fields = required_fields - history_detail_request.keys()
        
        if missing_fields:
            return {
                "error": f"Missing fields: {sorted(missing_fields)}"
            }, 400
            
        username = history_detail_request.get("Username")
        history_id = history_detail_request.get("HistoryId")
        
        if not isinstance(username, str):
            return {
                "error": "Username must be a string"
            }, 400
        
        if not isinstance(history_id, int):
            return {
                "error": "HistoryId must be an integer"
            }, 400
        
        try:
            detail, error = get_history_detail(history_id, username)
            
            if error:
                if "not found" in error:
                    return {
                        "error": error
                    }, 404
                return {
                    "error": error
                }, 500
            
            return {
                "message": "History detail retrieved successfully",
                "data": detail
            }, 200
        except Exception as e:
            return {
                "error": f"Failed to retrieve history detail: {e}"
            }, 500

    # -------------------------
    # ADMIN STUDENT HISTORY
    # -------------------------

    @app.route("/AdminUserHistory", methods=["POST"])
    def get_admin_user_history_data():
        data = request.get_json(silent=True) or {}
        if not isinstance(data, dict):
            return {"error": "Invalid JSON payload"}, 400

        required_fields = {"AdminUsername", "AdminPassword", "Username"}
        missing_fields = required_fields - data.keys()
        if missing_fields:
            return {"error": f"Missing fields: {sorted(missing_fields)}"}, 400

        history, error = get_admin_user_history(
            data.get("AdminUsername"),
            data.get("AdminPassword"),
            data.get("Username"),
        )
        if error == "Username not found" or error == "Incorrect password":
            return {"error": error}, 401
        if error:
            return {"error": error}, 500
        return {"message": "Admin history retrieved successfully", "data": history}, 200

    @app.route("/AdminHistoryDetail", methods=["POST"])
    def get_admin_history_detail_data():
        data = request.get_json(silent=True) or {}
        if not isinstance(data, dict):
            return {"error": "Invalid JSON payload"}, 400

        required_fields = {"AdminUsername", "AdminPassword", "Username", "HistoryId"}
        missing_fields = required_fields - data.keys()
        if missing_fields:
            return {"error": f"Missing fields: {sorted(missing_fields)}"}, 400
        if not isinstance(data.get("HistoryId"), int):
            return {"error": "HistoryId must be an integer"}, 400

        detail, error = get_admin_history_detail(
            data.get("AdminUsername"),
            data.get("AdminPassword"),
            data.get("Username"),
            data.get("HistoryId"),
        )
        if error == "History entry not found":
            return {"error": error}, 404
        if error == "Username not found" or error == "Incorrect password":
            return {"error": error}, 401
        if error:
            return {"error": error}, 500
        return {"message": "Admin history detail retrieved successfully", "data": detail}, 200

        
        
        
