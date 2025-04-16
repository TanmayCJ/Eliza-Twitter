from flask import Flask, request, jsonify
from image_captioner import ImageCaptioner  # Assuming the ImageCaptioner class is properly set up to handle image captioning

app = Flask(__name__)
captioner = ImageCaptioner()

@app.route("/caption", methods=["POST"])
def caption_handler():
    try:
        image_file = request.files.get('image', None)
        if not image_file:
            return jsonify({"error": "No image provided"}), 400
        
        caption = captioner.generate_caption(image_file)
        print(caption)
        return jsonify({"caption": caption})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9003)