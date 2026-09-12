import os
from dotenv import load_dotenv
from flask import Flask
from database.db import db
from database.models import User
from routes.routes import register_routes
from flask_cors import CORS
from flask_sock import Sock

load_dotenv()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
    "pool_timeout": 30,
    "connect_args": {"connect_timeout": 10},
}
CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

sock = Sock(app)

db.init_app(app)

register_routes(app, sock)

try:
    with app.app_context():
        db.create_all()
        # Migrate: add `standard` column to `users` if it doesn't exist yet.
        # db.create_all() only creates new tables, never alters existing ones.
        with db.engine.connect() as conn:
            from sqlalchemy import text, inspect
            inspector = inspect(db.engine)
            existing_columns = [col["name"] for col in inspector.get_columns("users")]
            if "standard" not in existing_columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN standard INTEGER"))
                conn.commit()
except Exception as e:
    print(f"Error creating database tables: {e}")

if __name__ == "__main__":
    app.run(debug=False)