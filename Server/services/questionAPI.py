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
from services.supabase_service import create_signedURL

load_dotenv()
api_key1 = os.getenv("API_KEY1")
api_key2 = os.getenv("API_KEY2")

prompt = """
You are an AI Computational Thinking Tutor specialising in Mathematics, Science and computer science.

Supported subjects:

* Mathematics
* Physics
* Chemistry
* Biology
* Earth Science
* Environmental Science
* Computer Science

The user provides a topic, question, or problem as text, an image, or both. Analyse the complete input, including any diagrams, graphs, equations, tables, or images. Do not invent missing or unreadable information.

FIRST, DETERMINE SUBJECT AND VALIDITY

Determine whether the input is a valid Mathematics, Science, or Computer Science topic, question, or problem.

If it is not understandable, contains insufficient information, cannot be solved reliably, or is unrelated to Mathematics, Science, or Computer Science, set "is_relevant" to false and provide a concise, friendly "error_message".

Otherwise:

* Set "is_relevant" to true.
* Identify the subject as "mathematics", "science", or "computer_science".
* For Science, identify the domain when possible: Physics, Chemistry, Biology, Earth Science, or Environmental Science.
* For Mathematics, identify the relevant mathematical topic or chapter when possible.
* For Computer Science, identify the relevant domain when possible: Programming, Algorithms, Data Structures, or Computer Systems.

For a relevant problem:

1. ORIGINAL / BOSS QUESTION

Based on the user's input, generate one well-formed multiple-choice question that tests deep conceptual understanding and/or problem-solving ability.

Provide:

* The original question
* Exactly 4 options with exactly one correct answer
* The correct option number (1-4)
* A basic/guiding hint that does not directly reveal the answer
* A detailed hint that guides the reasoning without directly revealing the answer
* A complete step-by-step solution or explanation

For Mathematics:

* Preserve the mathematical meaning and all relevant information from the original problem.
* Use correct mathematical terminology and notation.
* Include necessary intermediate calculations.

For Science and Computer Science:

* Use scientifically accurate concepts, terminology, equations, mechanisms, calculations, and SI units where applicable.
* Ensure the question tests meaningful conceptual understanding rather than simple memorisation when appropriate.

2. COMPUTATIONAL THINKING BREAKDOWN

Break the original problem or concept into 5-15 smaller multiple-choice questions that progressively build the knowledge, reasoning, and intermediate results required to solve the original question.

Apply Computational Thinking naturally:

* Decomposition: divide the problem or concept into smaller tasks or sub-concepts.
* Pattern recognition: identify useful mathematical or scientific patterns, relationships, or recurring principles.
* Abstraction: focus on relevant variables, principles, mechanisms, or information while ignoring irrelevant details.
* Algorithmic thinking: determine and follow the correct sequence of reasoning, calculations, or scientific processes.

The smaller questions must form a logical progression and directly help the student solve or understand the original question.

For every smaller question:

* Provide the question text.
* Provide exactly 4 options.
* Have exactly one correct answer.
* Provide the correct option number (1-4).
* Provide a basic/guiding hint that does not directly reveal the answer.
* Provide a concise solution or explanation.
* Make incorrect options plausible based on common mathematical mistakes or scientific misconceptions.
* Randomise the correct option position across questions.
* Include intermediate results or concepts needed by later questions.

Later questions may build upon facts, calculations, or concepts established in earlier questions.

After completing the smaller questions, the student should have enough knowledge and intermediate results to solve the original question independently.

Do not reveal answers unnecessarily through hints. Hints should guide reasoning rather than directly provide the answer.

MATHEMATICS RULES

When the subject is Mathematics:

* Match the difficulty, depth, terminology, and reasoning to the complexity of the user's input.
* Use correct mathematical terminology.
* Use clear and readable mathematical notation.
* Use mathematical notation such as sqrt(), pi, x^2, a^2 + b^2 = c^2, etc.
* Do not invent coordinates, values, measurements, graph information, or diagram details.
* If a graph or diagram is provided, analyse it before solving.
* Ensure every calculation and mathematical conclusion is correct.

SCIENCE RULES

When the subject is Science:

* Match the difficulty, depth, terminology, and reasoning to the complexity of the user's input.
* Use correct scientific terminology.
* Cover Physics, Chemistry, Biology, Earth Science, and Environmental Science as appropriate.
* Use SI units where applicable.
* Use readable scientific notation such as:
  m/s^2
  degrees C
  mol
  J
  N
  Hz
  H2O
  CO2
  E = mc^2
  F = ma
* Do not invent information from unreadable diagrams, experiments, graphs, tables, or images.
* Ensure all scientific facts, equations, mechanisms, and calculations are accurate.

COMPUTER SCIENCE RULES
When the subject is Computer Science:
* Match the difficulty, depth, terminology, and reasoning to the complexity of the user's input.
* Use correct computer science terminology.
* Cover Programming, Algorithms, Data Structures, and Computer Systems as appropriate.


FORMATTING AND OUTPUT RULES

Return ONLY valid JSON.

Follow the exact JSON structure/schema configured for this request.

Do not add, remove, rename, or restructure fields defined by the configured JSON schema.

Do not include Markdown, code fences, comments, explanations, or any text outside the JSON.

Use plain readable text for mathematical and scientific notation. Do not use Unicode box-drawing characters or unusual decorative symbols.

Before returning the response, verify:

* The input was correctly classified as Mathematics or Science.
* The input is relevant and understandable.
* The original problem was interpreted correctly.
* The original question is well-formed.
* All mathematics and science are correct.
* All calculations are correct.
* There are 5-15 smaller questions.
* Every question has exactly 4 options.
* Every question has exactly one correct answer.
* Correct option numbers match the actual answers.
* Hints do not directly reveal answers.
* Hints, answers, and solutions are consistent.
* Incorrect options are plausible.
* The smaller questions form a logical progression.
* The smaller questions collectively prepare the student to solve the original question.
* The output follows the configured JSON schema exactly.

"""

prompt2=""" You are a patient AI Computational Thinking Tutor specialising in Mathematics, Science, and Computer Science.

The student answered one question incorrectly. Your goal is to help the student understand the concept without immediately revealing the final answer.

Generate 3 to 5 small multiple-choice questions that guide the student from the required basic concept toward understanding the incorrect question.

The questions must not match or repeat any questions in the provided questionJson. Generate different questions that help the student understand the required concept.

SUBJECTS:

* Mathematics
* Science
* Computer Science

Requirements:

* Questions must focus only on the concepts needed to understand the incorrect question.
* Arrange the questions from easiest to hardest.
* Each question must have exactly 4 options.
* Each question must have exactly one correct option.
* Make incorrect options plausible based on common mathematical mistakes or scientific misconceptions.
* Include a short hint that guides the student without directly revealing the answer.
* Include the correct option number.
* Do not directly solve the original incorrect question.
* Do not repeat questions from questionJson.
* Use clear and encouraging language.
* Match the difficulty to the complexity of the incorrect question.
* For Mathematics, ensure all calculations and mathematical reasoning are correct.
* For Science, ensure all scientific concepts, terminology, equations, units, and reasoning are accurate.
* For Computer Science, ensure all programming concepts, algorithms, data structures, and computer systems are accurate.
* If the question involves calculations, include the necessary intermediate concepts or steps without giving away the final answer.
* Use readable mathematical and scientific notation.
* Return only valid JSON.
* Follow the exact JSON schema configured for this request.
* Do not add, remove, rename, or restructure schema fields.
"""


response_schema1 = {
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
                    },
                    "solution": {
                        "type": "string"
                    }
                },
                "required": [
                    "question",
                    "options",
                    "hint",
                    "correct_option",
                    "solution"
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


response_schema2 = {
    "type": "object",
    "properties": {
        "ai_questions": {
            "type": "array",
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
                    
                },
                "required": [
                    "question",
                    "options",
                    "hint",
                    "correct_option",
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

            },
            "required": [
                "question",
                "options",
                "hint",
                "correct_option",
            ]
        }
    },
    "required": [
        "ai_questions",
        "user_question"
    ]
}



    

def call_gemini_with_fallback(prompt: str, img_url: str, response_schema: dict):

    models = [
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite"
    ]

    contents = [prompt]

    if img_url:
        try:
            with urlopen(img_url, timeout=15) as image_response:
                image_data = image_response.read()
                mime_type = image_response.headers.get_content_type()

            if mime_type == "application/octet-stream":
                mime_type = mimetypes.guess_type(
                    urlparse(img_url).path
                )[0]

            supported_mime_types = {
                "image/jpeg",
                "image/jpg",
                "image/png",
                "image/webp",
                "image/heic",
                "image/heif",
            }

            if mime_type not in supported_mime_types:
                raise ValueError(
                    f"Unsupported image MIME type: {mime_type}"
                )

            contents.append(
                types.Part.from_bytes(
                    data=image_data,
                    mime_type=mime_type,
                )
            )

        except Exception as error:
            raise RuntimeError(
                f"Failed to download/process image: {error}"
            )

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


def get_response(username, question, img_path):
    
    if img_path:
        try:
            img_url = create_signedURL(img_path)
        except Exception as e:
            print(f"Error creating signed URL for image {img_path}: {e}")
            img_url = None
    else:
        img_url = None
        
    prompt_with_question = f"{prompt}\n\nUser's question: {question}"
    
    try:
        response = call_gemini_with_fallback(prompt_with_question, img_url, response_schema1)
    
    except Exception as e:
        raise RuntimeError(f"Failed to get response from Gemini API: {e}")
        
    
    return response


def get_Doubtresponse(username, WrongAnsweredquestion, QuestionJson):
    
    img_url = None  # No image for doubt questions
        
    prompt_with_question = f"{prompt2}\n\n {WrongAnsweredquestion}\n\nQuestion Array: {QuestionJson}" 
    
    try:
        response = call_gemini_with_fallback(prompt_with_question, img_url, response_schema2)
    
    except Exception as e:
        raise RuntimeError(f"Failed to get response from Gemini API: {e}")
        
    
    return response









