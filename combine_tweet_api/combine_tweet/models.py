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