from twitter_api_app.models import TwitterUser, Tweet

class TweetHandler:
    def __init__(self):
        pass

    def handle(self, data, data_type=None, user=None):
        """
        Process and save the given data.
        data_type must be 'user' or 'tweets'.
        If data_type is 'tweets', a TwitterUser instance must be passed as 'user'.
        """
        if not data_type:
            raise ValueError("data_type is required and must be 'user' or 'tweets'")

        if not data:
            raise ValueError("data is required and must be 'user' or 'tweets'")

        # Process and save user
        if data_type == "user":
            processed_user = self._process_user(data)
            return self._save_user(processed_user)

        # Process and save tweets (requires user)
        if data_type == "tweets":
            if user is None:
                raise ValueError("Saving tweets requires a TwitterUser instance to be passed as 'user'")
            processed_tweets = self._process_tweets(data)
            return self._save_tweets(processed_tweets, user)

        raise ValueError("Unknown data format. Specify data_type='user' or 'tweets'")

    # -----------------------
    # Processing
    # -----------------------

    def _process_user(self, user_data):
        return {
            "user_id": user_data.get("id"),
            "username": user_data.get("username"),
            "name": user_data.get("name"),
            "description": user_data.get("description"),
            "location": user_data.get("location"),
            "created_at": user_data.get("created_at"),
            "profile_image_url": user_data.get("profile_image_url"),
            "verified": user_data.get("verified", False),
            "protected": user_data.get("protected", False),
            "followers_count": user_data.get("public_metrics", {}).get("followers_count", 0),
            "following_count": user_data.get("public_metrics", {}).get("following_count", 0),
            "tweet_count": user_data.get("public_metrics", {}).get("tweet_count", 0),
            "listed_count": user_data.get("public_metrics", {}).get("listed_count", 0),
        }

    def _process_tweets(self, tweets_data):
        processed = []
        for tweet in tweets_data:
            public = tweet.get("public_metrics", {})
            non_public = tweet.get("non_public_metrics", {})
            organic = tweet.get("organic_metrics", {})
            entities = tweet.get("entities", {})

            processed.append({
                "tweet_id": tweet.get("id"),
                "text": tweet.get("text"),
                "created_at": tweet.get("created_at"),
                "retweet_count": public.get("retweet_count", 0),
                "reply_count": public.get("reply_count", 0),
                "like_count": public.get("like_count", 0),
                "quote_count": public.get("quote_count", 0),
                "impression_count": non_public.get("impression_count") or organic.get("impression_count"),
                "url_link_clicks": organic.get("url_link_clicks"),
                "user_profile_clicks": organic.get("user_profile_clicks"),
                "bookmark_count": non_public.get("bookmark_count"),
                "hashtags": entities.get("hashtags"),
                "mentions": entities.get("mentions"),
                "urls": entities.get("urls"),
                "symbols": entities.get("symbols"),
                "possibly_sensitive": tweet.get("possibly_sensitive", False),
            })
        return processed

    # -----------------------
    # Saving
    # -----------------------

    def _save_user(self, user_data):
        user, _ = TwitterUser.objects.update_or_create(
            user_id=user_data["user_id"],
            defaults=user_data
        )
        return user

    def _save_tweets(self, processed_tweets, user):
        saved = []
        for t in processed_tweets:
            if not Tweet.objects.filter(tweet_id=t["tweet_id"]).exists():
                tweet = Tweet.objects.create(
                    tweet_id=t["tweet_id"],
                    user=user,
                    text=t["text"],
                    created_at=t["created_at"],
                    retweet_count=t["retweet_count"],
                    reply_count=t["reply_count"],
                    like_count=t["like_count"],
                    quote_count=t["quote_count"],
                    impression_count=t.get("impression_count"),
                    url_link_clicks=t.get("url_link_clicks"),
                    user_profile_clicks=t.get("user_profile_clicks"),
                    bookmark_count=t.get("bookmark_count"),
                    hashtags=t.get("hashtags"),
                    mentions=t.get("mentions"),
                    urls=t.get("urls"),
                    symbols=t.get("symbols"),
                    possibly_sensitive=t.get("possibly_sensitive", False),
                )
                saved.append(tweet)
        return saved
