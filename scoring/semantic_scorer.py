from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer('all-MiniLM-L6-v2')

def semantic_score(jd_text, resume_text):
    # encode both texts into embeddings
    embeddings = model.encode([jd_text, resume_text])
    
    # cosine similarity returns value between 0 and 1
    score = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]    
    # return as 0-100
    return round(float(score) * 100)