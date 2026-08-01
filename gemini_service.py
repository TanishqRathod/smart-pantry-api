import os
import json

from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()


class GeminiService:

    def __init__(self):

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not found in .env file."
            )

        self.client = genai.Client(
            api_key=api_key
        )

        # Stable production model
        self.model = "gemini-3.5-flash"

    def generate_recipe(
        self,
        recipe_name,
        available,
        missing
    ):

        prompt = f"""
You are an expert chef and nutritionist.

Recipe Name:
{recipe_name}

Available Ingredients:
{", ".join(available) if available else "None"}

Missing Ingredients:
{", ".join(missing) if missing else "None"}

IMPORTANT RULES:

- Return ONLY valid JSON.
- Do NOT use Markdown.
- Do NOT wrap the JSON inside ```json.
- Do NOT add explanations before or after the JSON.
- Every field must exist.

Return exactly this structure:

{{
    "overview": "",

    "ingredients": [],

    "instructions": [],

    "nutrition": {{
        "calories": "",
        "protein": "",
        "carbohydrates": "",
        "fat": ""
    }},

    "substitutions": [],

    "storage": {{
        "fridge": "",
        "freezer": ""
    }},

    "variations": [],

    "tips": []
}}
"""

        try:

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )

            text = response.text.strip()

            # Remove markdown code fences if Gemini adds them
            text = text.replace("```json", "")
            text = text.replace("```", "")
            text = text.strip()

            return json.loads(text)

        except json.JSONDecodeError:

            return {
                "error": True,
                "message": "Gemini returned invalid JSON.",
                "raw_response": text if "text" in locals() else ""
            }

        except Exception as e:

            return {
                "error": True,
                "message": str(e)
            }