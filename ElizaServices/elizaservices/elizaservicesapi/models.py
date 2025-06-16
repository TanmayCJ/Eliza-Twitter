from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


# ------------------------------------------------------------------
# 1. SHARED ABSTRACT BASE CLASSES
# ------------------------------------------------------------------

class AbstractBaseTweet(models.Model):
    """Base fields for all tweets (posted or queued)."""
    content = models.TextField()
    hashtags = ArrayField(models.CharField(max_length=100), blank=True, null=True)
    image_urls = ArrayField(models.URLField(), blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class AbstractPostedTweet(AbstractBaseTweet):
    """Fields only for tweets that have been posted on Twitter."""
    tweet_id = models.CharField(max_length=50, unique=True)
    tweet_link = models.URLField(max_length=255)

    class Meta:
        abstract = True
        indexes = [models.Index(fields=["tweet_id"])]


# ------------------------------------------------------------------
# 2. CONCRETE POSTED TWEET MODELS FOR EACH BOT
# ------------------------------------------------------------------

class CarbonTruthTweet(AbstractPostedTweet):
    class Meta:
        db_table = "carbontruth_tweets"


class CarbonRantTweet(AbstractPostedTweet):
    class Meta:
        db_table = "carbonrant_tweets"


class DefaultTweet(AbstractPostedTweet):
    class Meta:
        db_table = "default_tweets"


class CarbonSustainAITweet(AbstractPostedTweet):
    class Meta:
        db_table = "carbonsustainai_tweets"


# ------------------------------------------------------------------
# 3. QUEUED TWEET MODEL FOR SCHEDULED POSTS
# ------------------------------------------------------------------

class AbstractQueuedTweet(AbstractBaseTweet):
    """Queued tweet to be posted by a specific bot at a given time."""

    BOT_CHOICES = [
        ("carbontruth", "CarbonTruth"),
        ("carbonsustainai", "CarbonSustainAI"),
        ("carbonrant", "CarbonRant"),
        ("default", "DefaultBot"),
    ]

    CATEGORY_CHOICES = [
        ("news", "News"),
        ("personal", "Personal"),
    ]

    url = models.URLField(blank=True, null=True)
    bot = models.CharField(max_length=30, choices=BOT_CHOICES)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    when_to_post = models.DateTimeField()

    class Meta:
        abstract = True
        ordering = ["when_to_post"]
        indexes = [models.Index(fields=["when_to_post"])]


class QueuedTweet(AbstractQueuedTweet):
    """Live queue table for tweets that will be posted later."""

    # Generic reference to actual posted tweet (if posted)
    content_type = models.ForeignKey(
        ContentType, on_delete=models.SET_NULL, null=True, blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    posted_tweet = GenericForeignKey("content_type", "object_id")

    class Meta:
        db_table = "queued_tweets"

    def is_posted(self):
        return self.content_type is not None and self.object_id is not None

    def mark_as_posted(self, instance):
        """Helper to link this queued tweet to the actual posted tweet."""
        self.content_type = ContentType.objects.get_for_model(instance)
        self.object_id = instance.id
        self.save(update_fields=["content_type", "object_id"])

    def __str__(self):
        status = "✅ posted" if self.is_posted() else "⏳ pending"
        return f"{self.bot} - {self.category} @ {self.when_to_post} → {status}"
