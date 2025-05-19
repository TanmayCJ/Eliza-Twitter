"""
tweet_knn.py
• Loads tweets.pkl and tweet_vecs.npy produced by build_tweet_index.py
• Provides top3_matches(query) → list[(tweet, similarity)]
"""
import pathlib, pickle, numpy as np
from sentence_transformers import SentenceTransformer

DATA_DIR    = pathlib.Path(".")            # same folder; change if needed
TEXT_FILE   = DATA_DIR / "tweets.pkl"
VEC_FILE    = DATA_DIR / "tweet_vecs.npy"
MODEL_NAME  = "all-MiniLM-L6-v2"

# --- load cached data ---
tweets     = pickle.loads(TEXT_FILE.read_bytes())
tweet_vecs = np.load(VEC_FILE)
print(f"Loaded {len(tweets)} tweets and vectors")

# --- lazy model load to keep import light ---
_model = None
def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model

# --- public API ---
def top3_matches(query: str):
    """Return list of (tweet, cosine_similarity_score) for the 3 best matches."""
    q_vec = _get_model().encode([query], normalize_embeddings=True)
    sims  = tweet_vecs @ q_vec.T           # dot == cosine (unit‑norm)
    sims  = sims.squeeze()
    idx   = np.argpartition(-sims, 3)[:3]
    idx   = idx[np.argsort(-sims[idx])]
    return [(tweets[i], float(sims[i])) for i in idx]

# --- demo when run directly ---
if __name__ == "__main__":
    for t, s in top3_matches("1/ Pump pain: California's gas prices soar to US highs! Supply and taxes drive costs up, with environmental fees adding $1.44/gallon. What's driving up your bill? https://tinyurl.com/4sd4p4m6 #GasPrices #Inflation #Sustainability"):
        print(f"{s:.3f}  {t}")
