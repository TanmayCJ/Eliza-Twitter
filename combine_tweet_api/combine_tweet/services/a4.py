"""
retrieve.py

• Loads cached:
    – tweets + tweet_vecs
    – company_chunks + chunk_vecs
• Provides:
    – top3_matches(query) → [(tweet, sim_score)…]
    – best_section(query) → (section_text, sim_score)
"""

import pickle, numpy as np
from sentence_transformers import SentenceTransformer
import os # Import the os module

# ── Config ─────────────────────────────────────────────────────────────────
# Get the directory of the current file (a4.py)
CURRENT_DIR = os.path.dirname(__file__)

# Use os.path.join to create paths relative to the current directory
TWEETS_PKL    = os.path.join(CURRENT_DIR, "tweets.pkl")
TWEETS_VEC    = os.path.join(CURRENT_DIR, "tweet_vecs.npy")
CHUNKS_PKL    = os.path.join(CURRENT_DIR, "company_chunks.pkl")
CHUNKS_VEC    = os.path.join(CURRENT_DIR, "chunk_vecs.npy")
MODEL_NAME    = "all-MiniLM-L6-v2"
# ────────────────────────────────────────────────────────────────────────────

# Load caches
# Ensure the data files exist at the paths defined above
try:
    tweets     = pickle.load(open(TWEETS_PKL, "rb"))
    tweet_vecs = np.load(TWEETS_VEC)
    chunks     = pickle.load(open(CHUNKS_PKL, "rb"))
    chunk_vecs = np.load(CHUNKS_VEC)
except FileNotFoundError as e:
    print(f"Error loading data files in a4.py: {e}")
    print("Please ensure the data files (tweets.pkl, tweet_vecs.npy, company_chunks.pkl, chunk_vecs.npy) are in the same directory as a4.py")
    # Depending on how critical this data is, you might want to raise the exception,
    # or handle it more gracefully (e.g., initialize empty lists/arrays and log a warning).
    # For now, printing an informative error. If the application crashes here,
    # it's because the data is essential.
    raise # Re-raise the exception so the program stops and you see the error clearly

# Lazy model loader
_model = None
def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model

def top3_matches(query: str):
    qv   = _get_model().encode([query], normalize_embeddings=True).squeeze()
    sims = tweet_vecs @ qv
    idx  = np.argpartition(-sims, 3)[:3]
    idx  = idx[np.argsort(-sims[idx])]
    return [(tweets[i], float(sims[i])) for i in idx]

def best_section(query: str):
    qv   = _get_model().encode([query], normalize_embeddings=True).squeeze()
    sims = chunk_vecs @ qv
    best = int(np.argmax(sims))
    return chunks[best], float(sims[best])

if __name__ == "__main__":
    test = "According to the EPA, chloroprene is a likely human carcinogen, and the Denka plant was emitting it at levels exceeding the agency's recommended threshold. This closure will significantly reduce the cancer risk for nearby communities."
    print("\nTop 3 matching tweets:")
    for t, s in top3_matches(test):
        print(f" {s:.3f}  {t}")

    sec, score = best_section(test)
    print(f"\nMost related PDF section (score {score:.3f}):\n{sec}")
