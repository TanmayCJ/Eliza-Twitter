# Standard Library
import json
import requests

# Django REST Framework
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# Local App
from .utils.caption_service.caption_service_handler import CaptionService
from .utils.popularity_service.popularity_service_handler import PopularityAPI
from .utils.safety_service.safety_service_handler import SafetyService
from .models import CarbonTruthTweet, CarbonRantTweet, DefaultTweet, CarbonSustainAITweet
from .serializers import (
    CarbonTruthTweetSerializer, CarbonRantTweetSerializer,
    DefaultTweetSerializer, CarbonSustainAITweetSerializer
)

caption_service = CaptionService()
popularity_service = PopularityAPI()
safety_service = SafetyService()

SENDER_MODEL_MAP = {
    'carbontruth': (CarbonTruthTweet, CarbonTruthTweetSerializer),
    'carbonrant': (CarbonRantTweet, CarbonRantTweetSerializer),
    'default': (DefaultTweet, DefaultTweetSerializer),
    'carbonsustainai': (CarbonSustainAITweet, CarbonSustainAITweetSerializer),
}

class PopularityScoreView(APIView):
    def post(self, request):
        tweet_text = request.data.get("text", "")
        image_file = request.FILES.get("image", None)
        
        if image_file:
            try:
                caption = caption_service.generate_caption(image_file)
                tweet_text += " " + caption
            except Exception as e:
                return Response({"error": "Failed to get caption: " + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            result = popularity_service.predict(tweet_text)
            return Response(result)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CompareHashtagsView(APIView):
    def post(self, request):
        text = request.data.get("text", "")
        hashtags = request.data.get("hashtags", [])
        top_n = request.data.get("top_n", len(hashtags))
        image_file = request.FILES.get("image", None)

        if image_file:
            try:
                caption = caption_service.generate_caption(image_file)
                text += " " + caption
            except Exception as e:
                return Response({"error": "Failed to get caption: " + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            result = popularity_service.compare_hashtags(text, hashtags, top_n)
            return Response(result)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SafetyScoreView(APIView):
    def post(self, request):
        text = request.data.get("text", "")
        image_file = request.FILES.get("image", None)

        response_data = {
            "text_safety_score": None,
            "image_safety_score": None
        }

        if image_file:
            try:
                caption = caption_service.generate_caption(image_file)
                image_safety_result = safety_service.check_text_safety(caption)
                response_data["image_safety_score"] = image_safety_result
            except Exception as e:
                return Response({"error": "Failed to process image: " + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if text:
            try:
                text_safety_result = safety_service.check_text_safety(text)
                response_data["text_safety_score"] = text_safety_result
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            response_data["text_safety_score"] = {"error": "No text provided for safety check."}

        return Response(response_data)

class TweetsView(APIView):
    def get(self, request):
        sender = request.query_params.get('sender', '').lower()
        if sender not in SENDER_MODEL_MAP:
            return Response(
                {"error": f"Invalid sender. Valid senders are: {list(SENDER_MODEL_MAP.keys())}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        model, serializer_class = SENDER_MODEL_MAP[sender]
        tweets = model.objects.all()
        serializer = serializer_class(tweets, many=True)
        return Response(serializer.data)

    def post(self, request):
        sender = request.data.get('sender', '').lower()
        if sender not in SENDER_MODEL_MAP:
            return Response(
                {"error": f"Invalid sender. Valid senders are: {list(SENDER_MODEL_MAP.keys())}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        model, serializer_class = SENDER_MODEL_MAP[sender]
        serializer = serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LatestTweetView(APIView):
    def get(self, request):
        sender = request.query_params.get('sender', '').lower()
        if sender not in SENDER_MODEL_MAP:
            return Response(
                {"error": f"Invalid sender. Valid senders are: {list(SENDER_MODEL_MAP.keys())}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        model, serializer_class = SENDER_MODEL_MAP[sender]
        latest_tweet = model.objects.order_by('-created_at').first()
        if not latest_tweet:
            return Response({"error": "No tweets found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = serializer_class(latest_tweet)
        return Response(serializer.data)

class SingleTweetView(APIView):
    def get(self, request, tweet_id):
        sender = request.query_params.get('sender', '').lower()
        if sender not in SENDER_MODEL_MAP:
            return Response(
                {"error": f"Invalid sender. Valid senders are: {list(SENDER_MODEL_MAP.keys())}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        model, serializer_class = SENDER_MODEL_MAP[sender]
        try:
            tweet = model.objects.get(tweet_id=tweet_id)
        except model.DoesNotExist:
            return Response({"error": "Tweet not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = serializer_class(tweet)
        return Response(serializer.data)

class ValidSendersView(APIView):
    def get(self, request):
        return Response(list(SENDER_MODEL_MAP.keys()), status=status.HTTP_200_OK)
