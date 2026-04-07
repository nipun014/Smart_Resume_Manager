import re


_MODEL = None
_MODEL_INIT_ATTEMPTED = False


def _token_overlap_score(jd_text, resume_text):
    jd_tokens = set(re.findall(r"[a-z0-9+#\.]+", (jd_text or "").lower()))
    resume_tokens = set(re.findall(r"[a-z0-9+#\.]+", (resume_text or "").lower()))
    if not jd_tokens:
        return 0
    overlap = len(jd_tokens & resume_tokens) / len(jd_tokens)
    return round(max(0.0, min(1.0, overlap)) * 100)


def _get_model():
    global _MODEL, _MODEL_INIT_ATTEMPTED
    if _MODEL is not None:
        return _MODEL
    if _MODEL_INIT_ATTEMPTED:
        return None

    _MODEL_INIT_ATTEMPTED = True
    try:
        from sentence_transformers import SentenceTransformer

        _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
        return _MODEL
    except Exception:
        return None


def semantic_score(jd_text, resume_text):
    model = _get_model()
    if model is None:
        return _token_overlap_score(jd_text, resume_text)

    try:
        from sklearn.metrics.pairwise import cosine_similarity

        embeddings = model.encode([jd_text or "", resume_text or ""])
        score = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        return round(float(score) * 100)
    except Exception:
        return _token_overlap_score(jd_text, resume_text)