from rest_framework import serializers
from .models import CarbonTruthTweet, CarbonRantTweet, DefaultTweet, CarbonSustainAITweet

class TweetSerializer(serializers.ModelSerializer):
    class Meta:
        model = None  # Will be set by child classes
        fields = ['id', 'tweet_id', 'date', 'time', 'content', 'tweet_link', 'hashtags', 'image_urls', 'created_at']

class CarbonTruthTweetSerializer(TweetSerializer):
    class Meta(TweetSerializer.Meta):
        model = CarbonTruthTweet

class CarbonRantTweetSerializer(TweetSerializer):
    class Meta(TweetSerializer.Meta):
        model = CarbonRantTweet

class DefaultTweetSerializer(TweetSerializer):
    class Meta(TweetSerializer.Meta):
        model = DefaultTweet

class CarbonSustainAITweetSerializer(TweetSerializer):
    class Meta(TweetSerializer.Meta):
        model = CarbonSustainAITweet