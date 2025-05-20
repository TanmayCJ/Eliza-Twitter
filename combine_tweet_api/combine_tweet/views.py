# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from combine_tweet.services.db_manager import DatabaseManager
# Remove or comment out the old TweetGenerator import
# from combine_tweet.services.tweet_generator import TweetGenerator
# Import the new TweetLLM class (adjust the path based on your project structure)
# Assuming 'new' is a top-level package
from combine_tweet.services.openai_inference import TweetLLM
from combine_tweet.services.branded_tweet_generator import BrandedTweetGenerator, get_branded_tweet
from combine_tweet.services.forced_branded_tweet_generator import get_forced_branded_tweet
from combine_tweet.services.url_processor import URLProcessor

# Removed the old TweetGenerator instance
# generator = TweetGenerator()
branded_generator = BrandedTweetGenerator()

# Instantiate the new TweetLLM
llm_generator = TweetLLM()

# Instantiate URLProcessor
url_processor = URLProcessor()

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

    # Use the new llm_generator and call its 'generate' method
    tweet = llm_generator.generate(factual_tweet=carbon_content, rant_tweet=rant_content)
    print(" the combines tweet is before url processing", "\n\n\n",tweet)

    # --- Force URL Appending ---
    # Extract URLs from source content
    _, carbon_urls = url_processor.extract_urls(carbon_content)
    _, rant_urls = url_processor.extract_urls(rant_content)
    all_source_urls = carbon_urls + rant_urls

    tweet_with_urls = tweet # Start with the generated tweet

    # Append the first found URL if any exist, regardless of length
    if all_source_urls:
        first_url = all_source_urls[0]
        # Ensure a space before appending the URL unless the tweet is empty
        if tweet_with_urls and not tweet_with_urls.endswith(' '):
             tweet_with_urls += ' '
        tweet_with_urls += first_url

    print(" the combines tweet is after force url appending", "\n\n\n", tweet_with_urls)
    # --- End Force URL Appending ---

    return Response({
        'tweet': tweet_with_urls, # Return the tweet with URL appended
        'sources': {
            'carbon_tweet': carbon_content,
            'rant_tweet': rant_content
        }
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

    # Use the new llm_generator and call its 'generate' method
    tweet = llm_generator.generate(factual_tweet=carbon_content, rant_tweet=rant_content)
    print(" the combines tweet is before url processing", "\n\n\n",tweet)

    # --- Force URL Appending ---
    # Extract URLs from source content
    url_processor_post = URLProcessor() # Instantiate locally for this function
    _, carbon_urls = url_processor_post.extract_urls(carbon_content)
    _, rant_urls = url_processor_post.extract_urls(rant_content)
    all_source_urls = carbon_urls + rant_urls

    tweet_with_urls = tweet # Start with the generated tweet

    # Append the first found URL if any exist, regardless of length
    if all_source_urls:
        first_url = all_source_urls[0]
        # Ensure a space before appending the URL unless the tweet is empty
        if tweet_with_urls and not tweet_with_urls.endswith(' '):
             tweet_with_urls += ' '
        tweet_with_urls += first_url

    print(" the combines tweet is after force url appending", "\n\n\n", tweet_with_urls)
    # --- End Force URL Appending ---

    return Response({
        'tweet': tweet_with_urls, # Return the tweet with URL appended
        'sources': {
            'carbon_tweet': carbon_content,
            'rant_tweet': rant_content
        }
    })

@api_view(['GET'])
def test(request):
    return Response({"message": "Test endpoint working"})

@api_view(['POST'])
def test_with_sample(request):
    data = request.data
    if 'carbon_tweet' not in data or 'rant_tweet' not in data:
        return Response({'error': 'Missing required sample tweets'}, status=400)

    tweet = llm_generator.generate(factual_tweet=data['carbon_tweet'], rant_tweet=data['rant_tweet'])

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

@api_view(['POST'])
def generate_branded_tweet(request):
    """
    Generate a branded tweet that always includes the company name.
    
    POST data:
    - fact_content: The factual content to include
    - context_content: The contextual content to include
    - fact_weight (optional): Weight for factual content (default: 0.7)
    - context_weight (optional): Weight for contextual content (default: 0.3)
    """
    data = request.data
    if 'fact_content' not in data or 'context_content' not in data:
        return Response({'error': 'Missing required content (fact_content and/or context_content)'}, status=400)
    
    # Get blend weights if provided, otherwise use defaults
    fact_weight = float(data.get('fact_weight', 0.7))
    context_weight = float(data.get('context_weight', 0.3))
    
    # Validate weights
    if abs((fact_weight + context_weight) - 1.0) > 0.01:
        return Response({
            'error': 'Blend weights must add up to 1.0',
            'provided': {'fact_weight': fact_weight, 'context_weight': context_weight}
        }, status=400)
    
    # Set blend ratio on generator
    branded_generator.set_blend_ratio(fact_weight, context_weight)
    
    # Generate the tweet
    tweet = branded_generator.generate_branded_tweet(
        data['fact_content'], 
        data['context_content']
    )
    
    return Response({
        'tweet': tweet,
        'tweet_length': len(tweet),
        'sources': {
            'fact_content': data['fact_content'],
            'context_content': data['context_content']
        },
        'blend_ratio': {
            'fact_weight': fact_weight,
            'context_weight': context_weight
        }
    })

@api_view(['GET'])
def generate_branded_from_latest(request):
    """
    Generate a branded tweet from the latest database entries.
    This will always include the company name in the tweet.
    """
    entries = DatabaseManager.get_latest_entries()
    fact_content = entries['carbon_tweet']['content'] or ""
    context_content = entries['rant_tweet']['content'] or ""
    
    # Get the tweet with brand name integration
    tweet = get_branded_tweet(fact_content, context_content)
    
    # Extra check for URLs in the tweet
    url_processor = URLProcessor()
    
    # Extract URLs from source content
    _, fact_urls = url_processor.extract_urls(fact_content)
    _, context_urls = url_processor.extract_urls(context_content)
    all_urls = fact_urls + context_urls
    
    # If we have URLs but they're not in the tweet, force append them
    if all_urls and not any(url in tweet for url in all_urls):
        tweet_text, existing_urls = url_processor.extract_urls(tweet)
        
        # Final, direct append if needed
        if len(tweet_text) < 240 - len(all_urls[0]) - 1:
            tweet = tweet_text + ' ' + all_urls[0]
    
    return Response({
        'tweet': tweet,
        'tweet_length': len(tweet),
        'sources': {
            'fact_content': fact_content,
            'context_content': context_content
        }
    })

@api_view(['GET'])
def generate_forced_branded_from_latest(request):
    """
    Generate a branded tweet from the latest database entries.
    This will ALWAYS include the company name, with no content suitability analysis.
    """
    entries = DatabaseManager.get_latest_entries()
    fact_content = entries['carbon_tweet']['content'] or ""
    context_content = entries['rant_tweet']['content'] or ""
    
    tweet = get_forced_branded_tweet(fact_content, context_content)
    
    return Response({
        'tweet': tweet,
        'tweet_length': len(tweet),
        'is_branded': True,
        'sources': {
            'fact_content': fact_content,
            'context_content': context_content
        }
    })
