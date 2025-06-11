from django.db import models
from django.contrib.postgres.fields import ArrayField

class BaseMainTweet(models.Model):
    content = models.TextField()
    hashtags = ArrayField(models.CharField(max_length=100), blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

class BaseTweet(BaseMainTweet):
    tweet_id = models.CharField(max_length=50, unique=True)
    tweet_link = models.URLField(max_length=255)
    image_urls = ArrayField(models.URLField(), blank=True, null=True)

    class Meta:
        abstract = True

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

class BaseQueuedTweet(BaseMainTweet):
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
        ('posted', 'Posted'),
    ]

    url = models.URLField(blank=True, null=True)
    bot = models.CharField(max_length=30, choices=BOT_CHOICES)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    when_to_post = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    class Meta:
        abstract = True

class QueuedTweet(BaseQueuedTweet):
    class Meta:
        db_table = 'queued_tweets'

    def __str__(self):
        return f"{self.bot} - {self.category} tweet scheduled at {self.when_to_post} [{self.status}]"
