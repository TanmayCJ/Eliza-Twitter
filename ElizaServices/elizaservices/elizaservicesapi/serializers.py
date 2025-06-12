from rest_framework import serializers
from .models import (
    CarbonTruthTweet,
    CarbonRantTweet,
    DefaultTweet,
    CarbonSustainAITweet,
    QueuedTweet
)

class CarbonTruthTweetSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarbonTruthTweet
        fields = [
            'id', 'tweet_id', 'content', 'tweet_link',
            'hashtags', 'image_urls', 'created_at'
        ]
        read_only_fields = ['created_at']

class CarbonRantTweetSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarbonRantTweet
        fields = [
            'id', 'tweet_id', 'content', 'tweet_link',
            'hashtags', 'image_urls', 'created_at'
        ]
        read_only_fields = ['created_at']

class DefaultTweetSerializer(serializers.ModelSerializer):
    class Meta:
        model = DefaultTweet
        fields = [
            'id', 'tweet_id', 'content', 'tweet_link',
            'hashtags', 'image_urls', 'created_at'
        ]
        read_only_fields = ['created_at']

class CarbonSustainAITweetSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarbonSustainAITweet
        fields = [
            'id', 'tweet_id', 'content', 'tweet_link',
            'hashtags', 'image_urls', 'created_at'
        ]
        read_only_fields = ['created_at']

class QueuedTweetSerializer(serializers.ModelSerializer):
    content = serializers.CharField()

    class Meta:
        model = QueuedTweet
        fields = [
            'id', 'content', 'hashtags', 'bot', 'category',
            'url', 'when_to_post', 'created_at', 'status'
        ]
        read_only_fields = ['created_at']
