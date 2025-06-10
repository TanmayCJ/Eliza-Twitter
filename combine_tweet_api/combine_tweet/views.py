# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from combine_tweet.services.db_manager import DatabaseManager
from combine_tweet.services.tweet_generator import TweetGenerator
from combine_tweet.services.url_processor import URLProcessor
from combine_tweet.models import CombinedTweetResult


# Use TweetGenerator for full pipeline (including safety/popularity checks)
generator = TweetGenerator()

# Instantiate URLProcessor
url_processor = URLProcessor()

def extract_safety_score(safety_data):
    if isinstance(safety_data, dict) and 'scores' in safety_data and safety_data['scores']:
        return max(safety_data['scores'].values())
    return None

def extract_popularity_score(popularity_data):
    if isinstance(popularity_data, dict):
        if 'predicted_score' in popularity_data:
            return popularity_data['predicted_score']
        if 'score' in popularity_data:
            return popularity_data['score']
    return None

@api_view(['GET'])
def home(request):
    return Response({"message": "CarbonSustain API is working"})

@api_view(['GET'])
def latest_entry(request):
    entries = DatabaseManager.get_latest_entries()
    return Response(entries)

@api_view(['GET'])
def generate_combined(request):
    entries = DatabaseManager.get_latest_entries()
    print(entries)
    carbon_content = entries['carbon_tweet']['content'] or ""
    rant_content = entries['rant_tweet']['content'] or ""
    print("truth tweet\n",carbon_content,"\n\nrant tweet\n\n" ,rant_content)
    result = generator.generate_combined_tweet(carbon_content, rant_content)
    tweet_with_urls = result['tweet']
    all_source_urls = result['extracted_urls']
    safety_score = result['safety_data']  # Store the full safety API result
    popularity_data = result['popularity_data']

    # Store in DB
    popularity_score = extract_popularity_score(popularity_data)

    CombinedTweetResult.objects.create(
        combined_tweet=tweet_with_urls,
        factual_tweet=carbon_content,
        rant_tweet=rant_content,
        extracted_urls=all_source_urls,
        popularity_score=popularity_score,
        safety_score=safety_score
    )

    return Response({
        'tweet': tweet_with_urls, # Return the tweet with URL appended
        'sources': {
            'carbon_tweet': carbon_content,
            'rant_tweet': rant_content
        },
        'safety_data': safety_score,
        'popularity_data': popularity_data,
        'extracted_urls': all_source_urls
    })

@api_view(['POST'])
def generate_combined_post(request):
    """
    Generate a combined tweet from carbon and rant tweet content provided
    in the request body, applying the same URL appending logic.
    """
    data = request.data
    if 'carbon_tweet' not in data or 'rant_tweet' not in data:
        return Response({'error': 'Missing required tweet content (carbon_tweet and/or rant_tweet)'}, status=400)

    carbon_content = data['carbon_tweet'] or ""
    rant_content = data['rant_tweet'] or ""

    print("truth tweet\n",carbon_content,"\n\nrant tweet\n\n" ,rant_content)

    # Use the generator to get the tweet and all metadata
    result = generator.generate_combined_tweet(carbon_content, rant_content)
    tweet_with_urls = result['tweet']
    all_source_urls = result['extracted_urls']
    safety_score = result['safety_data']  # Store the full safety API result
    popularity_data = result['popularity_data']

    # Store in DB
    popularity_score = extract_popularity_score(popularity_data)

    CombinedTweetResult.objects.create(
        combined_tweet=tweet_with_urls,
        factual_tweet=carbon_content,
        rant_tweet=rant_content,
        extracted_urls=all_source_urls,
        popularity_score=popularity_score,
        safety_score=safety_score
    )

    return Response({
        'tweet': tweet_with_urls, # Return the tweet with URL appended
        'sources': {
            'carbon_tweet': carbon_content,
            'rant_tweet': rant_content
        },
        'safety_data': safety_score,
        'popularity_data': popularity_data,
        'extracted_urls': all_source_urls
    })

@api_view(['GET'])
def test(request):
    return Response({"message": "Test endpoint working"})

@api_view(['POST'])
def test_with_sample(request):
    data = request.data
    if 'carbon_tweet' not in data or 'rant_tweet' not in data:
        return Response({'error': 'Missing required sample tweets'}, status=400)

    tweet = generator.generate_combined_tweet(data['carbon_tweet'], data['rant_tweet'])['tweet']

    # --- Force URL Appending for test_with_sample ---
    url_processor_test = URLProcessor() # Instantiate locally for this function
    _, carbon_urls_test = url_processor_test.extract_urls(data['carbon_tweet'])
    _, rant_urls_test = url_processor_test.extract_urls(data['rant_tweet'])
    all_source_urls_test = carbon_urls_test + rant_urls_test

    tweet_with_urls_test = tweet # Start with the generated tweet

    if all_source_urls_test:
        first_url_test = all_source_urls_test[0]
         # Ensure a space before appending the URL unless the tweet is empty
        if tweet_with_urls_test and not tweet_with_urls_test.endswith(' '):
             tweet_with_urls_test += ' '
        tweet_with_urls_test += first_url_test

    # --- End Force URL Appending ---


    return Response({
        'tweet': tweet_with_urls_test, # Return the tweet with URL appended
        'tweet_length': len(tweet_with_urls_test), # Return the length of the tweet with URL
        'sources': {
            'carbon_tweet': data['carbon_tweet'],
            'rant_tweet': data['rant_tweet']
        }
    })

