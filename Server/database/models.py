from database.db import db


class User(db.Model):
	__tablename__ = "users"

	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(80), nullable=False, unique=True)
	password = db.Column(db.String(255), nullable=False)



class QuestionsNScore(db.Model):
	__tablename__ = "questionsNScore"

	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(80), nullable=False)
	user_question = db.Column(db.Text, nullable=False)
	ai_questions = db.Column(db.Text, nullable=False)
	ai_answers = db.Column(db.Text, nullable=False)
	wrong_answered_question = db.Column(db.Text, nullable=True)
	score = db.Column(db.String(80), nullable=True)
