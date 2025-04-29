from django.db import models
from django.contrib.postgres.fields import ArrayField
from datetime import datetime

class BaseTweet(models.Model):
    tweet_id = models.CharField(max_length=50, unique=True)
    date = models.DateField()
    time = models.TimeField()
    content = models.TextField()
    tweet_link = models.URLField(max_length=255, blank=True, null=True)
    hashtags = ArrayField(models.CharField(max_length=100), blank=True, null=True)
    image_urls = ArrayField(models.URLField(), blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

    def to_dict(self):
        return {
            'id': self.id,
            'tweetID': self.tweet_id,
            'date': self.date.strftime('%Y-%m-%d'),
            'time': self.time.strftime('%H:%M:%S'),
            'content': self.content,
            'tweetLnk': self.tweet_link,
            'hashtags': self.hashtags,
            'imageUrl': self.image_urls,
            'created_at': self.created_at
        }

class CarbonTruthTweet(BaseTweet):
    class Meta:
        db_table = 'carbontruth_tweets'

class CarbonRantTweet(BaseTweet):
    class Meta:
        db_table = 'carbonrant_tweets'

class DefaultTweet(BaseTweet):
    class Meta:
        db_table = 'default_tweets'

class CarbonSustainAITweet(BaseTweet):
    class Meta:
        db_table = 'carbonsustainai_tweets'