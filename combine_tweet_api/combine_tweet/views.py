
# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from combine_tweet.services.db_manager import DatabaseManager
from combine_tweet.services.tweet_generator import TweetGenerator

generator = TweetGenerator()

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
