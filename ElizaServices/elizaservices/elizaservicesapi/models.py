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

class QueuedTweet(models.Model):
    BOT_CHOICES = [
        ('carbontruth', 'CarbonTruth'),
        ('carbonsustainai', 'CarbonSustainAI'),
        ('carbonrant', 'CarbonRant'),
    ]

    CATEGORY_CHOICES = [
        ('news', 'News'),
        ('personal', 'Personal'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('scheduled', 'Scheduled'),
        ('posted', 'Posted'),
        ('failed', 'Failed'),
    ]

    url = models.URLField(blank=True, null=True) 
    bot = models.CharField(max_length=30, choices=BOT_CHOICES)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    content = ArrayField(models.TextField())
    when_to_post = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    class Meta:
        db_table = 'queued_tweets'

    def __str__(self):
        return f"{self.bot} - {self.category} tweet(s) scheduled at {self.when_to_post}"
