# Standard Library
import json

# Django REST Framework
from rest_framework.views import APIView
from rest_framework.response import Response

# Local App
from .utils.caption_client import get_image_caption
from .utils.popularity_client import get_popularity_score
from .utils.safety_client import get_safety_score


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


class SafetyScoreView(APIView):
    def post(self, request):
        text = request.data.get("text", "")
        image_file = request.FILES.get("image", None)

        if image_file:
            caption_response = get_image_caption(image_file)
            if 'caption' in caption_response:
                text += " " + caption_response['caption']
            else:
                return Response({"error": "Failed to get caption"}, status=500)

        try:
            result = get_safety_score(text)
            # Include the cleaned text in the response
            cleaned_text = text
            result['cleaned_text'] = cleaned_text
            return Response(result)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
