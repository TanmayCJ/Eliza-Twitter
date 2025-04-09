from django.db import models

class TwitterUser(models.Model):
    user_id = models.CharField(max_length=50, unique=True)
    username = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    location = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)

    # Profile details
    profile_image_url = models.URLField(null=True, blank=True)
    verified = models.BooleanField(default=False)
    protected = models.BooleanField(default=False)

    # Public metrics
    followers_count = models.IntegerField(default=0)
    following_count = models.IntegerField(default=0)
    tweet_count = models.IntegerField(default=0)
    listed_count = models.IntegerField(default=0)

    # store the last used pagination token for continuing fetch
    last_pagination_token = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"@{self.username} ({self.user_id})"


class Tweet(models.Model):
    tweet_id = models.CharField(max_length=50, unique=True)
    user = models.ForeignKey(TwitterUser, on_delete=models.CASCADE, related_name="tweets")

    text = models.TextField()
    created_at = models.DateTimeField()

    retweet_count = models.IntegerField(default=0)
    reply_count = models.IntegerField(default=0)
    like_count = models.IntegerField(default=0)
    quote_count = models.IntegerField(default=0)

    # Non Public Metrics
    impression_count = models.IntegerField(null=True, blank=True)
    url_link_clicks = models.IntegerField(null=True, blank=True)
    user_profile_clicks = models.IntegerField(null=True, blank=True)
    bookmark_count = models.IntegerField(null=True, blank=True)

    # Entity Fields
    hashtags = models.JSONField(null=True, blank=True)
    mentions = models.JSONField(null=True, blank=True)
    urls = models.JSONField(null=True, blank=True)
    symbols = models.JSONField(null=True, blank=True)

    possibly_sensitive = models.BooleanField(default=False)

    def __str__(self):
        return f"Tweet {self.tweet_id} by @{self.user.username}"
