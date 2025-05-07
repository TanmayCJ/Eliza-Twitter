# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from combine_tweet.services.db_manager import DatabaseManager
from combine_tweet.services.tweet_generator import TweetGenerator
from combine_tweet.services.branded_tweet_generator import BrandedTweetGenerator, get_branded_tweet
from combine_tweet.services.forced_branded_tweet_generator import get_forced_branded_tweet

generator = TweetGenerator()
branded_generator = BrandedTweetGenerator()

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
    tweet = generator.generate_combined_tweet(carbon_content, rant_content)
    print(" the combines tweet is ", "\n\n\n",tweet)
    return Response({
        'tweet': tweet,
        'tweet_length': len(tweet),
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
    tweet = generator.generate_combined_tweet(data['carbon_tweet'], data['rant_tweet'])
    return Response({
        'tweet': tweet,
        'tweet_length': len(tweet),
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
    
    tweet = branded_generator.generate_branded_tweet(fact_content, context_content)
    
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
