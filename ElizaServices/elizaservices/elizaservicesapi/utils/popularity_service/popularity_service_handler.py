import os
from .popularity_bot import PopularityService

# Paths to your model and scaler files (adjust the path if necessary)
MODEL_PATH = os.path.join("elizaservicesapi", "utils", "popularity_service", "model", "popularity_model_100k_sc_out.pt")
SCALER_PATH = os.path.join("elizaservicesapi", "utils", "popularity_service", "model", "score_scaler.pkl")



class PopularityAPI:
    def __init__(self):
        # Initialize the PopularityService
        self.predictor = PopularityService(model_path=MODEL_PATH, scaler_path=SCALER_PATH)

    def predict(self, text: str) -> dict:
        """Predict the popularity score for a given text."""
        return self.predictor.predict(text)

    def compare_hashtags(self, text: str, hashtags: list, top_n: int) -> dict:
        """Compare hashtags and return the top N based on predicted scores."""
        scores = []
        for hashtag in hashtags:
            tweet_with_tag = f"{text} {hashtag}"
            result = self.predict(tweet_with_tag)
            scores.append({
                "hashtag": hashtag,
                "predicted_score": result.get("predicted_score")
            })

        # Sort descending and pick top N
        sorted_scores = sorted(scores, key=lambda x: x["predicted_score"], reverse=True)
        top_scores = sorted_scores[:top_n]

        return {"top_hashtags": top_scores}