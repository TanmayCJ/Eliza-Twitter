from flask import Flask, request, jsonify
from checker import SafetyChecker

app = Flask(__name__)
checker = SafetyChecker()

@app.route("/predict", methods=["POST"])
def predict_handler():
    try:
        data = request.get_json(force=True)
        if not data or "text" not in data:
            return jsonify({"error": "Missing 'text'"}), 400
        text = data["text"]
        result = checker.predict(text)

        # Convert possible bool/floats to something JSON-friendly
        safe_result = {
            "is_appropriate": bool(result["is_appropriate"]),
            "scores": {k: float(v) for k, v in result["scores"].items()},
            "explanation": result["explanation"]
        }
        return jsonify(safe_result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9002)