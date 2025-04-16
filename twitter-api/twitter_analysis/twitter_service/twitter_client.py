import requests
from django.conf import settings
from twitter_api_app.models import TwitterUser

class TwitterClient:
    """
    Uses the requests library to fetch tweets from Twitter API v2.
    This implementation uses bearer token authentication.
    """

    def __init__(self,
                 bearer_token: str = None,
                 consumer_key: str = None,
                 consumer_secret: str = None,
                 access_token: str = None,
                 access_token_secret: str = None):

        self.bearer_token = bearer_token or settings.TWITTER_BEARER_TOKEN
        print(self.bearer_token)
        self.consumer_key = consumer_key or settings.TWITTER_API_KEY
        self.consumer_secret = consumer_secret or settings.TWITTER_API_KEY_SECRET
        self.access_token = access_token or settings.TWITTER_ACCESS_TOKEN
        self.access_token_secret = access_token_secret or settings.TWITTER_ACCESS_TOKEN_SECRET

        # For requests, we're primarily using the bearer token.
        # If full OAuth1 credentials are provided, you would need to implement OAuth1 signing.
        self.use_user_auth = all([self.consumer_key, self.consumer_secret, self.access_token, self.access_token_secret])

    def get_headers(self):
        """Prepare the headers for authentication."""
        return {"Authorization": f"Bearer {self.bearer_token}"}

    def get_user_id(self, username: str) -> str:
        """
        Fetches a Twitter user by username and returns the user ID.
        Endpoint: GET https://api.twitter.com/2/users/by/username/:username
        """
        url = f"https://api.twitter.com/2/users/by/username/{username}"
        headers = self.get_headers()
        response = requests.get(url, headers=headers)
        print(response)
        if response.status_code != 200:
            raise Exception(f"Error fetching user 1: {response.text}")
        user_data = response.json()
        return user_data.get("data", {}).get("id")
    
    def get_user_detail(self, user_id: str) -> dict:
        """
        Fetches detailed information about a user by their user_id.
        Endpoint: GET https://api.twitter.com/2/users/:id
        """
        url = f"https://api.twitter.com/2/users/{user_id}"
        headers = self.get_headers()
        params = {
            "user.fields": "created_at,description,location,profile_image_url,public_metrics,verified,protected"
        }
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            if response.status_code != 200:
                raise Exception(f"Error fetching user: {response.text}")
        data = response.json()
        return data.get("data", {})

    def fetch_tweets(self, user_id: str, max_results: int = None, since_id: str = None):
        """
        Fetches tweets for a given user ID using pagination. If a token is present on 
        the user record, resume from there.
        """

        # 1. Load the user object from the database
        #    (Assuming the user record already exists. Otherwise, handle or create.)
        try:
            user_obj = TwitterUser.objects.get(user_id=user_id)
        except TwitterUser.DoesNotExist:
            raise Exception("TwitterUser record must exist before fetching tweets")

        url = f"https://api.twitter.com/2/users/{user_id}/tweets"
        tweet_fields = [
            "created_at", "public_metrics", "possibly_sensitive",
            "entities", "conversation_id"
        ]
        if self.use_user_auth:
            tweet_fields.append("non_public_metrics")

        headers = self.get_headers()
        all_tweets = []
        pagination_token = user_obj.last_pagination_token  # 2. Get the saved token
        per_page = 100  # Twitter's max allowed per page
        remaining = max_results if max_results is not None else float('inf')

        while remaining > 0:
            fetch_size = min(per_page, remaining) if max_results else per_page
            params = {
                "tweet.fields": ",".join(tweet_fields),
                "max_results": fetch_size
            }
            if since_id:
                params["since_id"] = since_id
            if pagination_token:
                # 3. If there's a stored token, use it
                params["pagination_token"] = pagination_token

            response = requests.get(url, headers=headers, params=params)
            if response.status_code != 200:
                print(f"Error fetching tweets: {response.text}")
                break

            data = response.json()
            tweets = data.get("data", [])
            all_tweets.extend(tweets)
            remaining -= len(tweets)

            meta = data.get("meta", {})
            new_pagination_token = meta.get("next_token")

            # 4. Update the user's token after each batch
            user_obj.last_pagination_token = new_pagination_token
            user_obj.save()

            # Prepare for next batch
            pagination_token = new_pagination_token
            if not pagination_token or not tweets:
                break  # No more data

        return all_tweets
