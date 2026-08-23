import os
from dotenv import load_dotenv
from flask import Flask
from database.db import db
from database.models import User
from routes.routes import register_routes
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
CORS(
    app,
    resources={r"/*": {"origins": ["http://localhost:5173"]}},
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

db.init_app(app)

register_routes(app)

try:
    with app.app_context():
        db.create_all()
except Exception as e:
    print(f"Error creating database tables: {e}")

if __name__ == "__main__":
    app.run(debug=True)