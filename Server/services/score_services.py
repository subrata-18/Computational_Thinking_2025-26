import os

from database.db import db
from database.models import User
from database.models import QuestionsNScore
import json
    
from dotenv import load_dotenv 
from google import genai


load_dotenv()
api_key1 = os.getenv("API_KEY1")
api_key2 = os.getenv("API_KEY2")

models = [
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite"
    ]




def get_remarks(QuestionJson, wrong_answered_questions, Score):
    prompt = f"""You are a teacher evaluating a student's performance on a computational thinking assessment. The assessment consists of multiple-choice questions, and the student's responses have been recorded. Your task is to provide constructive feedback based on the student's performance.
    The questions are given in the questionJson and the wrong answered questions are given in the wrong_answered_questions. The student's score is given in the Score.
    Please provide a brief summary of the student's performance, highlighting areas of strength and areas for improvement. Offer specific suggestions for how the student can enhance their understanding of computational thinking concepts.
    Your feedback should be brief, clear, concise, and encouraging, aiming to motivate the student to continue learning and improving their skills in computational thinking. It shouldn't be a huge paragraph, but rather very brief.
    QuestionJson: {QuestionJson}
    Wrong Answered Questions: {wrong_answered_questions}
    Score: {Score}"""
    
    for key_index, key in enumerate(
            (api_key1, api_key2),
            start=1
        ):
                
            client = genai.Client(api_key=key)
            
            for model in models:
                try:
                    response = client.models.generate_content(
                        model=model,
                        contents=prompt
                    )
                    return response.text
                except Exception as e:
                    print(f"Error with API key {key_index} and model {model}: {e}")
                    continue  # Try the next model or API key
                
    raise RuntimeError(
        "All Gemini attempts failed"
    )
                
     
     
     
     
     
def add_ScoreDB(username, QuestionJson, wrong_answered_questions, Score):
    # Create a new QuestionsNScore instance
    data=json.loads(QuestionJson)
    
    ai_questions = data["ai_questions"]

    # Store questions as JSON for reliable parsing
    ai_questions_json = json.dumps([q["question"] for q in ai_questions])
    
    # Store answers as JSON for reliable parsing (handles special characters)
    ai_answers_json = json.dumps([q["options"][q["correct_option"] - 1] for q in ai_questions])

    # Single user question
    user_question = data["user_question"]["question"]
    
    # Get remarks from AI - returns string directly
    try:
        remarks = get_remarks(QuestionJson, wrong_answered_questions, Score)
    except Exception as e:
        print(f"Error generating remarks: {e}")
        remarks = "Unable to generate remarks at this time."
    
    new_entry = QuestionsNScore(
        username=username,
        user_question=user_question,
        ai_questions=ai_questions_json, 
        ai_answers=ai_answers_json,     
        wrong_answered_question=wrong_answered_questions,
        score=Score,
        remarks=remarks
    )

    try:
        db.session.add(new_entry)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise Exception("Failed to add score entry to the database")