import os
import json
import mimetypes
from urllib.parse import urlparse
from urllib.request import urlopen

from google import genai
from google.genai import types
from database.db import db
from database.models import User
from dotenv import load_dotenv  

load_dotenv()
api_key1 = os.getenv("API_KEY1")
api_key2 = os.getenv("API_KEY2")

prompt = """
You are an AI Computational Thinking Mathematics Tutor.

The user provides a mathematics problem as text with coordinates for a graph. Analyze the complete problem, including the graph. Do not invent missing or unreadable information.

First, determine whether the input is a valid mathematics problem and can be solved graphically or not. If it is not, cannot be understood reliably, or is unrelated to the selected chapter, set "is_relevant" to false and provide a concise, friendly error_message and if it is a maths problem but not graphically solvable return the error message as,"This question cannot be solved graphically please switch to Standard Mode" Otherwise set it to true and continue.


IMPORTANT GRAPH AND COORDINATE RULES:

- Treat the provided coordinates as the source of truth for the graph.
- Do not invent, modify, approximate, or assume coordinates that were not provided.
- Every question you generate must be consistent with the provided coordinates.
- The coordinates field for each question must contain only the coordinate points that are relevant to understanding or solving that specific question.
- Do not automatically copy all original coordinates into every question.
- Select the minimum relevant coordinates needed for each question.
- A smaller question must be directly understandable and solvable using the coordinates provided for that question.
- If a smaller question refers to a point, line, intersection, vertex, endpoint, intercept, slope, distance, region, or other graphical feature, include the coordinates required to identify that feature.
- If a question requires multiple points, include all of those relevant points in its coordinates field.
- If a question requires the entire graph to understand the relationship, include all relevant coordinates needed to reconstruct that relationship.
- Never create a question that requires coordinates which are not present in that question's coordinates field.
- Coordinate order must always be [x, y].
- Coordinates must be returned as:
  [[x1, y1], [x2, y2], ...]
- The coordinates field must contain between 1 and 4 coordinate pairs according to the configured schema.
- If more than 4 coordinates are necessary to understand a graphical question, restructure the question so that no more than 4 relevant coordinate pairs are required.
- Use the coordinates to make each question visually meaningful, not merely as additional data.

For example, if the original graph contains:
[[1, 2], [3, 6], [5, 10]]

and a smaller question asks about the point at x = 3, its coordinates should contain:
[[3, 6]]

If a smaller question asks about the relationship between the first and second points, its coordinates should contain:
[[1, 2], [3, 6]]

If a smaller question asks about the complete relationship represented by all three points, its coordinates may contain:
[[1, 2], [3, 6], [5, 10]]

Do not include irrelevant coordinates.



For a relevant problem:

1. ORIGINAL/BOSS QUESTION
Generate 4 multiple-choice options with exactly one correct answer. Also provide:
- the original question
- correct option
- a hint for the original question
- the coordinates of the graph (if any) in a structured format
- The coordinates should be returned in an array of array format [[x1, y1], [x2, y2], ...] for each question in the coordinates field in the schema.

2. COMPUTATIONAL THINKING BREAKDOWN
Break the original problem into 5–15 smaller multiple-choice questions that progressively build the knowledge and intermediate results required to solve the original problem with coordinates for graph for each question
The coordinates should be returned in an array of array format [[x1, y1], [x2, y2], ...] for each question in the coordinates field in the schema.

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
- Include the coordinates of the graph in a structured format.
- The coordinates should be returned in an array of array format [[x1, y1], [x2, y2], ...] for each question in the coordinates field in the schema.
- Make incorrect options plausible mistakes.
- Randomize the correct option position.
- Include intermediate results needed by later questions.

The student should have enough knowledge and intermediate results after completing the smaller questions to solve the original problem independently.

Do not reveal answers unnecessarily through hints. Hints should guide reasoning rather than directly give the answer.

Match the difficulty and mathematical level of the original problem. The AI response must contain proper mathematical symbols like √(sqrt), π(pi), exponents(²) etc and do not use unicode characters.

Return ONLY valid JSON and follow the exact JSON structure/schema configured for this request. Do not add, remove, rename, or restructure fields. Do not include Markdown, code fences, explanations, or text outside the JSON.

Before returning, verify:
- The original problem was interpreted correctly.
- All mathematics is correct.
- There are 5–15 smaller questions.
- Every question has exactly 4 options and one correct answer.
- Each question has coordinates for the graph. The coordinates should be returned in an array of array format [[x1, y1], [x2, y2], ...] for each question.
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
                        },
                        "coordinates": {
                            "type": "array",
                            "minItems": 1,
                            "maxItems": 4,
                            "items": {
                                "type": "array",
                                "minItems": 2,
                                "maxItems": 2,
                                "items": {
                                    "type": "number"
                                }
                            }
                        }
                    },
                    "required": [
                        "question",
                        "options",
                        "hint",
                        "correct_option",
                        "coordinates"
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
                    },
                    "coordinates": {
                        "type": "array",
                        "minItems": 0,
                        "maxItems": 4,
                        "items": {
                            "type": "array",
                            "minItems": 2,
                            "maxItems": 2,
                            "items": {
                                "type": "number"
                            }
                        }
                    }
                },
                "required": [
                    "question",
                    "options",
                    "hint",
                    "correct_option",
                    "coordinates"
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


def call_gemini_with_fallback(prompt: str, response_schema: dict):

    models = [
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite"
    ]

    contents = [prompt]


    # ------------------------------------------------
    # Gemini fallback
    # ------------------------------------------------

    for key_index, key in enumerate(
        (api_key1, api_key2),
        start=1
    ):

        client = genai.Client(api_key=key)

        for model in models:

            try:

                print(
                    f"Trying key {key_index}, model {model}"
                )

                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=response_schema,
                    ),
                )

                if response.parsed is not None:
                    print(
                        f"Success: key {key_index}, model {model}"
                    )
                    print(f"Pahrased response is returned")

                    return response.parsed

                if response.text:
                    print(
                        f"Success: key {key_index}, model {model}"
                    )
                    print(f"Text response is returned:")
                    return json.loads(response.text)

                raise RuntimeError(
                    "Gemini returned an empty response"
                )

            except Exception as error:

                print(
                    f"Failed: key {key_index}, "
                    f"model {model}: "
                    f"{type(error).__name__}: {error}"
                )

                continue

    raise RuntimeError(
        "All Gemini attempts failed"
    )
    
    
    
def get_graphical_response(username, question, coordinates):
        
    prompt_with_question = f"{prompt}\n\nUser's question: {question}\n\nCoordinates:{json.dumps(coordinates)}"
    
    try:
        response = call_gemini_with_fallback(prompt_with_question, response_schema)
    
    except Exception as e:
        raise RuntimeError(f"Failed to get response from Gemini API: {e}")
        
    
    return response
