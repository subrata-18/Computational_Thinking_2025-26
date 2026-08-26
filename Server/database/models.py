from database.db import db


class User(db.Model):
	__tablename__ = "users"

	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(80), nullable=False, unique=True)
	password = db.Column(db.String(255), nullable=False)

	def __repr__(self):
		return f"<User {self.username}>"

class Question(db.Model):
	__tablename__ = "questions"

	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(80), nullable=False)
	question_text = db.Column(db.Text, nullable=False)
	question_img = db.Column(db.String(255), nullable=True)
	ai_questions = db.Column(db.Text, nullable=False)
	ai_answers = db.Column(db.Text, nullable=False)
