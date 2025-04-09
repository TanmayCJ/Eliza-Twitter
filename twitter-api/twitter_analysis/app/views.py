from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from app.models import TwitterUser, Tweet
from .utils import analyze_tweets_for_user

class TwitterAnalysisView(APIView):
    def post(self, request, format=None):
        twitter_handle = request.data.get("twitter_handle")
        tweet_count = request.data.get("tweet_count")
        if not twitter_handle:
            return Response({"error": "twitter_handle is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Try converting tweet_count to int, default to None if invalid
        try:
            tweet_count = int(tweet_count)
            if tweet_count < 1:
                return Response({"error": "tweet count invalid"}, status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, TypeError):
            tweet_count = None
        
        try:
            count = analyze_tweets_for_user(twitter_handle, tweet_count)
            return Response({
                "message": f"Successfully fetched and stored {count} tweets.",
                "handle": twitter_handle
            })
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TwitterDisplayView(APIView):
    def post(self, request, format=None):
        # Retrieve query parameters
        twitter_handle = request.data.get("twitter_handle")
        tweet_count = request.data.get("tweet_count")

        if not twitter_handle:
            return Response(
                {"error": "twitter_handle query parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Try converting tweet_count to int, or set to None if not valid
        try:
            tweet_count = int(tweet_count)
            if tweet_count < 1:
                return Response({"error": "tweet_count must be a positive integer."}, status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, TypeError):
            tweet_count = None  # If tweet_count is missing or invalid, fetch all tweets

        try:
            user = TwitterUser.objects.get(username=twitter_handle)
        except TwitterUser.DoesNotExist:
            return Response(
                {"error": f"Twitter user with handle '{twitter_handle}' not found in our database."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"Error retrieving Twitter user: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        try:
            tweets_qs = Tweet.objects.filter(user=user).order_by("-created_at")
            if not tweets_qs.exists():
                return Response(
                    {"message": f"No tweets found for user '{twitter_handle}'."},
                    status=status.HTTP_200_OK
                )

            # Limit tweet count if provided
            if tweet_count is not None:
                tweets_qs = tweets_qs[:tweet_count]

            tweet_data = []
            for tweet in tweets_qs:
                tweet_data.append({
                    "tweet_id": tweet.tweet_id,
                    "text": tweet.text,
                    "created_at": tweet.created_at,
                    "retweet_count": tweet.retweet_count,
                    "reply_count": tweet.reply_count,
                    "like_count": tweet.like_count,
                    "quote_count": tweet.quote_count,
                    "impression_count": tweet.impression_count,
                    "url_link_clicks": tweet.url_link_clicks,
                    "user_profile_clicks": tweet.user_profile_clicks,
                    "bookmark_count": tweet.bookmark_count,
                    "hashtags": tweet.hashtags,
                    "mentions": tweet.mentions,
                    "urls": tweet.urls,
                    "symbols": tweet.symbols,
                    "possibly_sensitive": tweet.possibly_sensitive,
                })

            return Response(
                {
                    "tweets": tweet_data,
                    "message": f"Found {len(tweet_data)} tweet(s) for user '{twitter_handle}'."
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": f"Error retrieving tweets: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )