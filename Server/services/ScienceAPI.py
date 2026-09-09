import os
import json
import mimetypes
from urllib.parse import urlparse
from urllib.request import urlopen

from google import genai
from google.genai import types
from dotenv import load_dotenv
from services.supabase_service import create_signedURL

load_dotenv()
api_key1 = os.getenv("API_KEY1")
api_key2 = os.getenv("API_KEY2")

science_prompt = """
You are an AI Science Tutor specialising in science (Physics, Chemistry, Biology,
Earth Science, and Environmental Science)

The user provides a science topic, question, or problem as text, an image, or both.
Analyse the complete input including any diagrams or images.
Do not invent missing or unreadable information.

First, determine whether the input is a valid science topic or problem.
If it is not, cannot be understood reliably, or is completely unrelated to science,
set "is_relevant" to false and provide a concise, friendly error_message.
Otherwise set it to true and continue.

For a relevant science problem:

1. ORIGINAL / BOSS QUESTION
Based on the user's topic or problem, generate one well-formed multiple-choice question that
tests deep conceptual understanding. Provide:
- The question text
- Exactly 4 options with exactly one correct answer
- The correct option number (1–4)
- A guiding hint that does NOT directly reveal the answer
- A complete, step-by-step explanation/solution

2. SCAFFOLDING QUESTIONS (5–15 questions)
Break the concept down into 5–15 smaller multiple-choice questions that progressively build
the knowledge required to answer the original question.

Apply Computational Thinking naturally:
- Decomposition   : break the concept into smaller sub-concepts or steps.
- Pattern recognition : identify recurring scientific principles or relationships.
- Abstraction     : focus on the key variables or mechanisms; ignore irrelevant detail.
- Algorithmic thinking: sequence the reasoning steps logically.

For every scaffolding question:
- Provide exactly 4 options with exactly one correct answer.
- Include the question text.
- Include the correct option number (1–4).
- Give a guiding hint that does NOT directly reveal the answer.
- Give a concise solution/explanation.
- Make incorrect options plausible misconceptions students commonly hold.
- Randomise the correct option position across questions.
- Build on intermediate facts established by earlier questions so each question
  prepares the ground for the next.

After completing all scaffolding questions the student should have enough understanding
to attempt the original/boss question independently.

Additional rules:
- Use correct scientific terminology and SI units where applicable.
- Include relevant symbols and units written in plain readable text
  (e.g. "m/s^2", "degrees C", "mol", "J", "N", "Hz", "H2O", "CO2", "E = mc^2", "F = ma").
- Do NOT use unicode box-drawing characters or unusual symbols.
- Do not reveal answers through hints; hints must guide reasoning only.
- Match difficulty to school level (classes 6–12).
- Span all major science domains as appropriate: Physics, Chemistry, Biology, Earth Science.

Return ONLY valid JSON following the exact schema configured for this request.
Do not add markdown, code fences, or any text outside the JSON.

Before returning, verify:
- The original question is correctly formed and scientifically accurate.
- All science facts and calculations are correct.
- There are between 5 and 15 scaffolding questions.
- Every question has exactly 4 options and one correct answer.
- Hints, answers, and solutions are all consistent with each other.
- The scaffolding questions collectively prepare the student to solve the original question.
- The output follows the configured JSON schema exactly.
"""

# Identical schema to questionAPI response_schema1 (no coordinates field needed)
response_schema = {
    "type": "object",
    "properties": {
        "is_relevant": {"type": "boolean"},
        "error_message": {"type": "string"},
        "ai_questions": {
            "type": "array",
            "minItems": 5,
            "maxItems": 15,
            "items": {
                "type": "object",
                "properties": {
                    "question":       {"type": "string"},
                    "options":        {
                        "type": "array",
                        "minItems": 4,
                        "maxItems": 4,
                        "items": {"type": "string"},
                    },
                    "hint":           {"type": "string"},
                    "correct_option": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 4,
                    },
                },
                "required": ["question", "options", "hint", "correct_option"],
            },
        },
        "user_question": {
            "type": "object",
            "properties": {
                "question":       {"type": "string"},
                "options":        {
                    "type": "array",
                    "minItems": 4,
                    "maxItems": 4,
                    "items": {"type": "string"},
                },
                "hint":           {"type": "string"},
                "correct_option": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 4,
                },
                "solution": {"type": "string"},
            },
            "required": ["question", "options", "hint", "correct_option", "solution"],
        },
    },
    "required": ["is_relevant", "error_message", "ai_questions", "user_question"],
}


def call_science_gemini(prompt_text: str, img_url: str | None):
    """Try both API keys × both models; return the first successful parsed response."""
    models = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]

    contents = [prompt_text]

    if img_url:
        try:
            with urlopen(img_url, timeout=15) as img_resp:
                image_data = img_resp.read()
                mime_type  = img_resp.headers.get_content_type()

            if mime_type == "application/octet-stream":
                mime_type = mimetypes.guess_type(urlparse(img_url).path)[0]

            supported = {
                "image/jpeg", "image/jpg", "image/png",
                "image/webp", "image/heic", "image/heif",
            }
            if mime_type not in supported:
                raise ValueError(f"Unsupported image MIME type: {mime_type}")

            contents.append(
                types.Part.from_bytes(data=image_data, mime_type=mime_type)
            )

        except Exception as error:
            raise RuntimeError(f"Failed to download/process image: {error}")

    for key_index, key in enumerate((api_key1, api_key2), start=1):
        client = genai.Client(api_key=key)
        for model in models:
            try:
                print(f"[ScienceAPI] Trying key {key_index}, model {model}")
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=response_schema,
                    ),
                )

                if response.parsed is not None:
                    print(f"[ScienceAPI] Success (parsed): key {key_index}, model {model}")
                    return response.parsed

                if response.text:
                    print(f"[ScienceAPI] Success (text): key {key_index}, model {model}")
                    return json.loads(response.text)

                raise RuntimeError("Gemini returned an empty response")

            except Exception as error:
                print(
                    f"[ScienceAPI] Failed: key {key_index}, model {model}: "
                    f"{type(error).__name__}: {error}"
                )
                continue

    raise RuntimeError("All Gemini attempts failed (ScienceAPI)")


def get_science_response(username: str, question: str, img_path: str):
    """
    Main entry point called by the /ScienceQuestionPost route.
    Mirrors get_response() in questionAPI.py.
    """
    img_url = None
    if img_path:
        try:
            img_url = create_signedURL(img_path)
        except Exception as e:
            print(f"[ScienceAPI] Error creating signed URL for {img_path}: {e}")

    prompt_with_question = (
        f"{science_prompt}\n\nUser's science topic / question: {question}"
    )

    try:
        return call_science_gemini(prompt_with_question, img_url)
    except Exception as e:
        raise RuntimeError(f"Failed to get response from Gemini API (Science): {e}")
