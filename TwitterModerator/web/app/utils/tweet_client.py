import requests

def get_tweets(params=None):
    """
    Get tweets from the database storage service
    
    Args:
        params: Query parameters to filter tweets
        
    Returns:
        JSON response from the database storage service
    """
    url = "http://database_storage:9004/api/tweets"
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def create_tweet(data):
    """
    Create a new tweet in the database storage service
    
    Args:
        data: Tweet data to create
        
    Returns:
        JSON response from the database storage service
    """
    url = "http://database_storage:9004/api/tweets"
    response = requests.post(url, json=data)
    response.raise_for_status()
    return response.json()

def get_latest_tweet(sender=None):
    """
    Get the latest tweet from the database storage service
    
    Args:
        sender: Optional sender to filter tweets
        
    Returns:
        JSON response from the database storage service
    """
    url = "http://database_storage:9004/api/tweets/latest"
    params = {}
    if sender:
        params['sender'] = sender
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def get_tweet_by_id(tweet_id, sender=None):
    """
    Get a specific tweet by ID from the database storage service
    
    Args:
        tweet_id: ID of the tweet to retrieve
        sender: Optional sender to filter tweets
        
    Returns:
        JSON response from the database storage service
    """
    url = f"http://database_storage:9004/api/tweets/{tweet_id}"
    params = {}
    if sender:
        params['sender'] = sender
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def get_valid_senders():
    """
    Get a list of valid senders from the database storage service
    
    Returns:
        JSON response from the database storage service
    """
    url = "http://database_storage:9004/api/senders"
    response = requests.get(url)
    response.raise_for_status()
    return response.json() 