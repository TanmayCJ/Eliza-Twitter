# Standard Library
import json

# Django REST Framework
from rest_framework.views import APIView
from rest_framework.response import Response

# Local App
from .utils.caption_client import get_image_caption
from .utils.popularity_client import get_popularity_score, get_top_hashtags
from .utils.safety_client import get_safety_score, get_image_safety_score


class PopularityScoreView(APIView):
    def post(self, request):
        tweet_text = request.data.get("text", "")
        image_file = request.FILES.get("image", None)
        
        if image_file:
            caption_response = get_image_caption(image_file)
            if 'caption' in caption_response:
                tweet_text += " " + caption_response['caption']
            else:
                return Response({"error": "Failed to get caption"}, status=500)

        try:
            result = get_popularity_score(tweet_text)
            return Response(result)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class CompareHashtagsView(APIView):
    def post(self, request):
        text = request.data.get("text", "")
        hashtags = request.data.get("hashtags", [])
        top_n = request.data.get("top_n", len(hashtags))
        image_file = request.FILES.get("image", None)

        # reuse image captioning if an image is provided
        if image_file:
            caption_response = get_image_caption(image_file)
            if 'caption' in caption_response:
                text += " " + caption_response['caption']
            else:
                return Response({"error": "Failed to get caption"}, status=500)

        try:
            result = get_top_hashtags(text, hashtags, top_n)
            return Response(result)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class SafetyScoreView(APIView):
    def post(self, request):
        text = request.data.get("text", "")
        image_file = request.FILES.get("image", None)

        # Initialize response structure
        response_data = {
            "text_safety_score": None,
            "image_safety_score": None
        }

        if image_file:
            # Call the image safety check function
            try:
                image_safety_result = get_image_safety_score(image_file)
                response_data["image_safety_score"] = image_safety_result
            except Exception as e:
                return Response({"error": str(e)}, status=500)

        if text:
            # Call the text safety check function
            try:
                text_safety_result = get_safety_score(text)
                response_data["text_safety_score"] = text_safety_result
            except Exception as e:
                return Response({"error": str(e)}, status=500)
        else:
            # If no text is provided, indicate that the text safety score is not applicable
            response_data["text_safety_score"] = {"error": "No text provided for safety check."}

        return Response(response_data)
