from django.db import models

class CarbonTruthTweet(models.Model):
    content = models.TextField()
    image_urls = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'carbontruth_tweets'
        ordering = ['-created_at']

class CarbonRantTweet(models.Model):
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'carbonrant_tweets'
        ordering = ['-created_at']

class CombinedTweetResult(models.Model):
    combined_tweet = models.TextField()
    factual_tweet = models.TextField()
    rant_tweet = models.TextField()
    extracted_urls = models.JSONField(default=list)
    popularity_score = models.JSONField(null=True, blank=True)  # or FloatField if just a number
    safety_score = models.JSONField(null=True, blank=True)      # or FloatField if just a number
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'combined_tweet_results'
        ordering = ['-created_at']