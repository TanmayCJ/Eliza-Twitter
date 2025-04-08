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

if __name__ == "__main__":
    # Run on port 9001 and expose on all interfaces to suit Docker setups.
    app.run(host="0.0.0.0", port=9001)