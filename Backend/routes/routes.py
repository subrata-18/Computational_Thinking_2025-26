from flask import request

def register_routes(app):

    @app.route("/")
    def home():
        return {"message": "Backend is running"}

    @app.route("/data", methods=["POST"])
    def receive_data():
        data = request.get_json()

        return {
            "message": "Data received",
            "data": data
        }