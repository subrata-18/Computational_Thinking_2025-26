from database.db import db


class User(db.Model):
	__tablename__ = "users"

	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(80), nullable=False, unique=True)
	password = db.Column(db.String(255), nullable=False)
	email_id = db.Column(db.String(120), nullable=False, unique=True)

	def __repr__(self):
		return f"<User {self.username}>"
