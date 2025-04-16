from twitter_service.twitter_client import TwitterClient
from twitter_service.tweet_handler import TweetHandler

def analyze_tweets_for_user(twitter_handle: str, max_results: int):
    """
    High-level utility function to fetch, process, and save tweets 
    for a given user handle.
    """

    client = TwitterClient()
    handler = TweetHandler()

    # Get and save user
    user_id = client.get_user_id(twitter_handle)
    raw_user = client.get_user_detail(user_id)
    user_obj = handler.handle(raw_user, data_type="user")

    # Get and save tweets (pass user_obj explicitly)
    raw_tweets = client.fetch_tweets(user_id, max_results=max_results)
    tweets = handler.handle(raw_tweets, data_type="tweets", user=user_obj)

    return len(tweets)
