import os
from dotenv import load_dotenv
from google import genai

load_dotenv()  # Loads variables from .env in project root if present.

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY is not set. Add it to a .env file at the project root.")

client = genai.Client(api_key=api_key)

# Try stable model ids in order; first available one is used.
MODEL_CANDIDATES = [
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash-latest",
]


def _generate_with_fallback(prompt):
    last_error = None
    for model_name in MODEL_CANDIDATES:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            if getattr(response, "text", None):
                return response.text
            return str(response)
        except Exception as exc:
            last_error = exc

    # Fail soft so scoring output remains usable even if Gemini is unavailable.
    if last_error:
        return (
            "Justification unavailable right now because the Gemini API request failed "
            f"({last_error})."
        )
    return "Justification unavailable right now because no model candidates were configured."

def generate_justification(jd_text, resume_text, score):
    prompt = f"""
    You are a recruiter assistant.
    
    Job Description:
    {jd_text}
    
    Candidate Resume:
    {resume_text}
    
    Match Score: {score}%
    
    Write exactly 2 sentences explaining why this candidate 
    is or isn't a good fit. Be specific about skills and experience.
    """
    
    return _generate_with_fallback(prompt)
