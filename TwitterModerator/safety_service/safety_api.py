import os
from flask import Flask, request, jsonify
from checker import SafetyChecker
from dotenv import load_dotenv
import boto3

app = Flask(__name__)
checker = SafetyChecker()
load_dotenv()

print(os.getenv('AWS_REGION'))
print(os.getenv('AWS_ACCESS_KEY_ID'))
print(os.getenv('AWS_SECRET_ACCESS_KEY'))


# Initialize Rekognition client
rekognition_client = boto3.client(
    'rekognition',
    region_name=os.getenv('AWS_REGION'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)


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
    
@app.route("/image_check", methods=["POST"])
def image_check_handler():
    try:
        # Get the image file from the request
        image_file = request.files.get('image', None)
        if not image_file:
            return jsonify({"error": "No image provided"}), 400

        # Load image bytes
        image_bytes = image_file.read()

        # Call Rekognition to detect unsafe content
        response = rekognition_client.detect_moderation_labels(
            Image={'Bytes': image_bytes},
            MinConfidence=75
        )

        # Process the response
        moderation_labels = response.get('ModerationLabels', [])
        results = []
        for label in moderation_labels:
            results.append({
                "Name": label['Name'],
                "Confidence": label['Confidence']
            })

        return jsonify({"moderation_labels": results})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9002)