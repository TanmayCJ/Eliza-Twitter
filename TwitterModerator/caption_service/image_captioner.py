from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image

class ImageCaptioner:
    def __init__(self):
        # Load BLIP model and processor
        self.processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        self.model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

    def generate_caption(self, image_file):
        # Open the uploaded image file using PIL
        image = Image.open(image_file.stream).convert("RGB")

        # Preprocess image
        inputs = self.processor(image, return_tensors="pt")
        
        # Generate caption
        output = self.model.generate(**inputs)
        caption = self.processor.decode(output[0], skip_special_tokens=True)

        return caption
