import boto3
from PIL import Image
from django.conf import settings

class ImageCaptioner:
    def __init__(self):
        # Initialize Rekognition client
        self.rekognition_client = boto3.client(
            'rekognition',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )

    def generate_caption(self, image_file):
        # Read the image file
        image_bytes = image_file.read()
        
        # Use AWS Rekognition to detect labels
        response = self.rekognition_client.detect_labels(
            Image={'Bytes': image_bytes},
            MaxLabels=10,
            MinConfidence=70
        )
        
        # Extract labels and create a caption
        labels = [label['Name'] for label in response.get('Labels', [])]
        
        if labels:
            caption = "This image contains: " + ", ".join(labels)
        else:
            caption = "No recognizable objects found in this image."
            
        return caption
