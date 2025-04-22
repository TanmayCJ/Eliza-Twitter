from flask import Flask, request, jsonify
from predictor import PopularityPredictor
import os

# Paths to your model and scaler files (adjust the path if necessary)
MODEL_PATH = os.path.join("model", "popularity_model_100k_sc_out.pt")
SCALER_PATH = os.path.join("model", "score_scaler.pkl")

# Create the predictor at startup so that it loads only once.
predictor = PopularityPredictor(model_path=MODEL_PATH, scaler_path=SCALER_PATH)

app = Flask(__name__)

@app.route("/predict", methods=["POST"])
def predict_handler():
    data = request.get_json()
    text = data.get("text", "")
    result = predictor.predict(text)
    return jsonify(result)

@app.route("/compare_hashtags", methods=["POST"])
def compare_hashtags_handler():
    data = request.get_json()
    text = data.get("text", "")
    hashtags = data.get("hashtags", [])
    top_n = data.get("top_n", len(hashtags))

    scores = []
    for hashtag in hashtags:
        tweet_with_tag = f"{text} {hashtag}"
        result = predictor.predict(tweet_with_tag)
        scores.append({
            "hashtag": hashtag,
            "predicted_score": result.get("predicted_score")
        })

    # sort descending and pick top N
    sorted_scores = sorted(scores, key=lambda x: x["predicted_score"], reverse=True)
    print(sorted_scores)
    top_scores = sorted_scores[:top_n]

    return jsonify({"top_hashtags": top_scores})

if __name__ == "__main__":
    # Run on port 9001 and expose on all interfaces to suit Docker setups.
    app.run(host="0.0.0.0", port=9001)