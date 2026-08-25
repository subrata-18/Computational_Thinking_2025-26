import os
import json

from google import genai
from google.genai import types
from database.db import db
from database.models import User
from database.models import Question



def call_gemini_with_fallback(prompt: str, response_schema: dict, api_key1: str, api_key2: str):
    models = ["gemini-3-flash", "gemini-3.5-flash","gemini-3.5-flash-lite","gemini-3.1-flash-lite"]
    last_error = None

    for key in (api_key1, api_key2):
        try:
            client = genai.Client(api_key=key)

            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=response_schema,
                ),
            )

            # Handle parsed JSON response if available
            if hasattr(response, "parsed") and response.parsed is not None:
                return response.parsed

            # Fallback for text response
            if hasattr(response, "text") and response.text:
                return json.loads(response.text)

            # If model returns something unexpected, raise to trigger fallback
            raise ValueError("Empty Gemini response")

        except Exception as exc:
            last_error = exc
            print(f"Gemini request failed with key: {key[:8]}... -> {exc}")
            continue

    raise RuntimeError(f"All Gemini API keys failed. Last error: {last_error}")


def get_response(username, question, img_url):
    api_key1 = os.getenv("API_KEY1")
    api_key2 = os.getenv("API_KEY2")

    prompt = """
You are an AI Computational Thinking Mathematics Tutor.

The user provides a mathematics problem as text, an image, or both. Analyze the complete problem, including any diagrams/images. Do not invent missing or unreadable information.

First, determine whether the input is a valid mathematics problem. If it is not, cannot be understood reliably, or is unrelated to the selected chapter, set "is_relevant" to false and provide a concise, friendly error_message. Otherwise set it to true and continue.

For a relevant problem:

1. ORIGINAL/BOSS QUESTION
Generate 4 multiple-choice options with exactly one correct answer. Also provide:
- the original question
- correct option
- a basic hint
- a detailed hint
- a complete step-by-step solution

2. COMPUTATIONAL THINKING BREAKDOWN
Break the original problem into 5–15 smaller multiple-choice questions that progressively build the knowledge and intermediate results required to solve the original problem.

Use Computational Thinking naturally:
- Decomposition: divide the problem into smaller tasks.
- Pattern recognition: identify useful mathematical patterns or relationships.
- Abstraction: focus on relevant information.
- Algorithmic thinking: determine the correct sequence of operations.

The smaller questions must form a logical progression and directly help the student solve the original problem.

For every smaller question:
- Provide exactly 4 options with exactly one correct answer.
- Include the question text.
- Include the correct option.
- Give a basic hint.
- Give a concise solution.
- Make incorrect options plausible mistakes.
- Randomize the correct option position.
- Include intermediate results needed by later questions.

The student should have enough knowledge and intermediate results after completing the smaller questions to solve the original problem independently.

Do not reveal answers unnecessarily through hints. Hints should guide reasoning rather than directly give the answer.

Match the difficulty and mathematical level of the original problem.

Return ONLY valid JSON and follow the exact JSON structure/schema configured for this request. Do not add, remove, rename, or restructure fields. Do not include Markdown, code fences, explanations, or text outside the JSON.

Before returning, verify:
- The original problem was interpreted correctly.
- All mathematics is correct.
- There are 5–15 smaller questions.
- Every question has exactly 4 options and one correct answer.
- Hints, answers, and solutions are consistent.
- The smaller questions collectively prepare the student to solve the original problem.
- The output follows the configured JSON schema exactly.
"""

    response_schema = {
        "type": "object",
        "properties": {
            "is_relevant": {
                "type": "boolean"
            },
            "error_message": {
                "type": "string"
            },
            "ai_questions": {
                "type": "array",
                "minItems": 5,
                "maxItems": 15,
                "items": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string"
                        },
                        "options": {
                            "type": "array",
                            "minItems": 4,
                            "maxItems": 4,
                            "items": {
                                "type": "string"
                            }
                        },
                        "hint": {
                            "type": "string"
                        },
                        "correct_option": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 4
                        }
                    },
                    "required": [
                        "question",
                        "options",
                        "hint",
                        "correct_option"
                    ]
                }
            },
            "user_question": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string"
                    },
                    "options": {
                        "type": "array",
                        "minItems": 4,
                        "maxItems": 4,
                        "items": {
                            "type": "string"
                        }
                    },
                    "hint": {
                        "type": "string"
                    },
                    "correct_option": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 4
                    }
                },
                "required": [
                    "question",
                    "options",
                    "hint",
                    "correct_option"
                ]
            }
        },
        "required": [
            "is_relevant",
            "error_message",
            "ai_questions",
            "user_question"
        ]
    }
    
    


