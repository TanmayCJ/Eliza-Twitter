# Standard Library
import json
import requests
from django.utils import timezone
from django.http import Http404

# Django REST Framework
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# Local App
from .utils.caption_service import CaptionService
from .utils.popularity_service import PopularityAPI
from .utils.safety_service import SafetyService
from .utils.news_service import NewsService
from .utils.imagegen_service import ImageGenServiceHandler
from .utils.text_emotion_service import TextEmotionService
from .models import CarbonTruthTweet, CarbonRantTweet, DefaultTweet, CarbonSustainAITweet, QueuedTweet
from .serializers import (
    CarbonTruthTweetSerializer, CarbonRantTweetSerializer,
    DefaultTweetSerializer, CarbonSustainAITweetSerializer, QueuedTweetSerializer
)

caption_service = CaptionService()
popularity_service = PopularityAPI()
safety_service = SafetyService()
text_emotion_service = TextEmotionService()


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

class EnvironmentalNewsView(APIView):
    def get(self, request):
        countries = request.query_params.getlist("country") or ["US", "CA"]
        try:
            news_service = NewsService(countries)
            news_data = news_service.fetch_environmental_news()
            return Response(news_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TweetsView(APIView):
    def get(self, request):
        sender = request.query_params.get("sender", "").lower()

        if sender not in SENDER_MODEL_MAP:
            return Response(
                {"error": f"Invalid sender. Valid senders are: {list(SENDER_MODEL_MAP.keys())}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        model, serializer_class = SENDER_MODEL_MAP[sender]
        tweets = model.objects.all()
        serializer = serializer_class(tweets, many=True)
        return Response(serializer.data)

    def post(self, request):
        sender = request.data.get("sender", "").lower()
        queued_id = request.query_params.get("queued_id", None)  # changed: now from query params

        if sender not in SENDER_MODEL_MAP:
            return Response(
                {"error": f"Invalid sender. Valid senders are: {list(SENDER_MODEL_MAP.keys())}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        model, serializer_class = SENDER_MODEL_MAP[sender]
        serializer = serializer_class(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # If queued_id is given, validate it BEFORE saving the tweet
        match = None
        if queued_id:
            from .models import QueuedTweet
            match = QueuedTweet.objects.filter(
                id=queued_id,
                bot=sender,
                content_type__isnull=True,
                object_id__isnull=True,
            ).first()

            if not match:
                return Response(
                    {"error": f"No unposted QueuedTweet with id={queued_id} for bot '{sender}'."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Save the tweet
        instance = serializer.save()

        # Link the queued tweet if matched
        if match:
            match.mark_as_posted(instance)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

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

class LatestNTweetsView(APIView):
    def get(self, request):
        sender = request.query_params.get('sender', '').lower()
        count = request.query_params.get('count', 5)

        if sender not in SENDER_MODEL_MAP:
            return Response(
                {"error": f"Invalid sender. Valid senders are: {list(SENDER_MODEL_MAP.keys())}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            count = int(count)
            if count <= 0:
                raise ValueError
        except ValueError:
            return Response({"error": "Count must be a positive integer."}, status=status.HTTP_400_BAD_REQUEST)

        model, serializer_class = SENDER_MODEL_MAP[sender]
        latest_tweets = model.objects.order_by('-created_at')[:count]
        serializer = serializer_class(latest_tweets, many=True)
        return Response(serializer.data)

class ValidSendersView(APIView):
    def get(self, request):
        return Response(list(SENDER_MODEL_MAP.keys()), status=status.HTTP_200_OK)

class ImageGenView(APIView):
    def post(self, request):
        keyword = request.data.get("keyword", "")
        if not keyword:
            return Response({"error": "Keyword is required."}, status=status.HTTP_400_BAD_REQUEST)
        imagegen_handler = ImageGenServiceHandler()
        image_url = imagegen_handler.fetch_image(keyword)
        return Response({"image_url": image_url})

class QueuedTweetView(APIView):
    def post(self, request):
        sender = request.data.get("sender", "").lower()

        if sender not in SENDER_MODEL_MAP:
            return Response(
                {"error": f"Invalid sender. Valid senders are: {list(SENDER_MODEL_MAP.keys())}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        now = timezone.now()

        # Updated logic: find only unposted tweets
        queued = QueuedTweet.objects.filter(
            bot=sender,
            content_type__isnull=True,
            object_id__isnull=True,
            when_to_post__lte=now
        ).order_by("when_to_post").first()

        if not queued:
            return Response({"message": "No queued tweets ready to post."}, status=status.HTTP_404_NOT_FOUND)

        serializer = QueuedTweetSerializer(queued)
        return Response(serializer.data, status=status.HTTP_200_OK)
