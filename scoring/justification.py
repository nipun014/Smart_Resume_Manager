import os
import threading
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()  # Loads variables from .env in project root if present.

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY is not set. Add it to a .env file at the project root.")

client = genai.Client(api_key=api_key)


MODEL_CANDIDATES = [
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash-latest",
]

# When a model hits quota/rate limits, park it briefly and fail over to the next one.
MODEL_RATE_LIMIT_COOLDOWN_SECONDS = 90
_RATE_LIMIT_MARKERS = (
    "429",
    "rate limit",
    "too many requests",
    "resource_exhausted",
    "quota",
)

_MODEL_STATE_LOCK = threading.Lock()
_MODEL_STATE = {
    name: {
        "cooldown_until": 0.0,
        "last_error": None,
    }
    for name in MODEL_CANDIDATES
}
def _is_rate_limited(exc):
    text = str(exc).lower()
    return any(marker in text for marker in _RATE_LIMIT_MARKERS)


def _discover_available_models():
    """Removed dynamic model discovery to prevent severe performance regression."""
    return []


def _get_attempt_order():
    """Return models in strict priority order, with cooled-down models moved to the back."""
    now = time.monotonic()
    available = list(MODEL_CANDIDATES)
    for model_id in _discover_available_models():
        if model_id not in available:
            available.append(model_id)

    with _MODEL_STATE_LOCK:
        for model_id in available:
            if model_id not in _MODEL_STATE:
                _MODEL_STATE[model_id] = {"cooldown_until": 0.0, "last_error": None}

        ready = [
            model_id
            for model_id in available
            if _MODEL_STATE[model_id]["cooldown_until"] <= now
        ]
        cooling = [
            model_id
            for model_id in available
            if _MODEL_STATE[model_id]["cooldown_until"] > now
        ]

    return ready + cooling


def _register_success(model_name):
    with _MODEL_STATE_LOCK:
        _MODEL_STATE[model_name]["cooldown_until"] = 0.0
        _MODEL_STATE[model_name]["last_error"] = None


def _register_failure(model_name, exc):
    with _MODEL_STATE_LOCK:
        _MODEL_STATE[model_name]["last_error"] = str(exc)
        if _is_rate_limited(exc):
            _MODEL_STATE[model_name]["cooldown_until"] = (
                time.monotonic() + MODEL_RATE_LIMIT_COOLDOWN_SECONDS
            )


def _generate_with_fallback(prompt):
    last_error = None
    for model_name in _get_attempt_order():
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            if getattr(response, "text", None):
                _register_success(model_name)
                return response.text
            _register_success(model_name)
            return str(response)
        except Exception as exc:
            last_error = exc
            _register_failure(model_name, exc)

    # Fail soft so scoring output remains usable even if Gemini is unavailable.
    if last_error:
        return (
            "Justification unavailable right now because the Gemini API request failed "
            f"({last_error})."
        )
    return "Justification unavailable right now because no model candidates were configured."


def generate_justification(
    jd_text,
    resume_text,
    score,
    jd_skills=None,
    candidate_skills=None,
    scores=None,
    profile=None,
):
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
