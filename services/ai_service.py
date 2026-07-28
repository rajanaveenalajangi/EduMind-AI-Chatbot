import os
from google import genai
from google.genai import types
from google.genai.errors import APIError

# Models confirmed available to new Gemini API keys as of July 2026.
# "gemini-2.5-flash-lite" (the old default below) has been retired for
# new users, which is the exact cause of the "no longer available to
# new users" error. See: https://ai.google.dev/gemini-api/docs/deprecations
SUPPORTED_MODELS = {
    "gemini-3.5-flash",        # general-purpose, best price/performance
    "gemini-3.1-flash-lite",   # fast/cheap tier, direct replacement for gemini-2.5-flash-lite
    "gemini-3.1-pro-preview",  # heavier reasoning tier
}
DEFAULT_MODEL = "gemini-3.1-flash-lite"


class AIService:
    def __init__(self):
        # Read parameters from environment variables
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.model_name = self._resolve_model(
            os.environ.get("GEMINI_MODEL", DEFAULT_MODEL)
        )

        # Initialize client if API key is provided
        self.client = None

        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)

                print("===== AVAILABLE MODELS =====")
                for model in self.client.models.list():
                    print(model.name)
                print("============================")

            except Exception as e:
                print(f"Error initializing Gemini Client: {e}")

    @staticmethod
    def _resolve_model(requested_model):
        """
        Validate the requested model name against the list of models
        currently available to new API keys. This prevents a stale
        GEMINI_MODEL env var (or a missing one) from silently pointing
        at a retired model like "gemini-2.5-flash-lite".
        """
        if requested_model in SUPPORTED_MODELS:
            return requested_model

        print(
            f"Warning: model '{requested_model}' is not in the supported "
            f"list {sorted(SUPPORTED_MODELS)}. Falling back to '{DEFAULT_MODEL}'."
        )
        return DEFAULT_MODEL

    def generate_response(self, prompt, history_messages=None):
        """
        Sends the user prompt and recent conversation history to the Gemini API.
        
        history_messages: A list of message objects or dicts with 'role' and 'content'
        """
        if not self.api_key or not self.client:
            return {
                "success": False,
                "error": "EduMind AI is not configured. Please add a valid GEMINI_API_KEY to your .env file."
            }

        if not prompt.strip():
            return {
                "success": False,
                "error": "The prompt cannot be empty."
            }

        # System instruction to configure the Student Assistant personality
        system_instruction = (
            "You are EduMind AI, a helpful student learning assistant. "
            "Your behavior guidelines:\n"
            "- Explain concepts simply and step-by-step, using appropriate terminology.\n"
            "- Provide clear programming examples (Python, SQL, HTML, CSS, JavaScript basics).\n"
            "- Help with coding debugging, explaining errors simply.\n"
            "- Support exam preparation, placement preparation tips, and study plans.\n"
            "- Support explanations in English and Telugu (explain in Telugu when the user asks, e.g., 'Explain this topic in Telugu' or uses Telugu words).\n"
            "- Keep explanation levels suited to a B.Tech/college student."
        )

        try:
            # Prepare content including history
            contents = []
            
            if history_messages:
                for msg in history_messages:
                    # Map db roles to Gemini roles ('user' -> 'user', 'assistant' -> 'model')
                    gemini_role = "user" if msg.role == "user" else "model"
                    contents.append(
                        types.Content(
                            role=gemini_role,
                            parts=[types.Part.from_text(text=msg.content)]
                        )
                    )

            # Append the current prompt
            contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=prompt)]
                )
            )

            # Configure request parameters
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7,
            )

            # Generate content from the model
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config
            )

            if response and response.text:
                return {
                    "success": True,
                    "text": response.text
                }
            else:
                return {
                    "success": False,
                    "error": "Received an empty response from EduMind AI. Please try again."
                }

        except APIError as e:
            # Handle standard Gemini API errors (e.g. invalid API key, quota limit)
            print(f"Gemini API Error: {e}")
            if "API_KEY_INVALID" in str(e) or e.code == 400:
                return {
                    "success": False,
                    "error": "Invalid API Key. Please verify your GEMINI_API_KEY in the .env file."
                }
            return {
                "success": False,
                "error": f"API Error: {e.message if hasattr(e, 'message') else str(e)}"
            }
        except Exception as e:
            # Handle other errors (network connection timeouts, etc.)
            print(f"Unexpected Error during AI generation: {e}")
            return {
                "success": False,
                "error": "A network or connection error occurred. Please check your internet connection and try again."
            }