# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from combine_tweet.services.db_manager import DatabaseManager
from combine_tweet.services.tweet_generator import TweetGenerator
from combine_tweet.services.url_processor import URLProcessor
from combine_tweet.models import CombinedTweetResult
import logging
from django.db.models import Q

class TweetViewHandler:
    def __init__(self):
        self.generator = TweetGenerator()
        self.url_processor = URLProcessor()

    def extract_safety_score(self, safety_data):
        if not isinstance(safety_data, dict):
            return None
        
        # Create a new concise structure
        concise_safety_data = {
            'is_appropriate': None,
            'scores': {},
            'image_safety_score': None
        }
        
        # Extract text safety score data
        if 'text_safety_score' in safety_data:
            text_safety = safety_data['text_safety_score']
            if isinstance(text_safety, dict):
                concise_safety_data['is_appropriate'] = text_safety.get('is_appropriate')
                if 'scores' in text_safety:
                    concise_safety_data['scores'] = text_safety['scores']
        
        # Get image_safety_score from the root level
        concise_safety_data['image_safety_score'] = safety_data.get('image_safety_score')
        
        return concise_safety_data

    def extract_popularity_score(self, popularity_data):
        if isinstance(popularity_data, dict):
            if 'predicted_score' in popularity_data:
                return popularity_data['predicted_score']
            if 'score' in popularity_data:
                return popularity_data['score']
        return None

    def validate_generation_result(self, result):
        """Validate that all required fields are present and valid in the generation result"""
        required_fields = ['tweet', 'extracted_urls', 'safety_data', 'popularity_data']
        
        # Check if all required fields exist
        if not all(field in result for field in required_fields):
            return False, "Missing required fields in generation result"
        
        # Check if tweet is valid
        if not result['tweet'] or len(result['tweet']) < 20:
            return False, "Generated tweet is invalid or too short"
        
        # Check if safety data is valid
        if not result['safety_data'] or not isinstance(result['safety_data'], dict):
            return False, "Invalid safety data"
        
        # Check if popularity data is valid
        if not result['popularity_data'] or not isinstance(result['popularity_data'], dict):
            return False, "Invalid popularity data"
        
        return True, "Validation successful"

    def check_tweets_already_used(self, carbon_content, rant_content):
        """
        Check if these exact tweets have been used before in a successful generation
        """
        try:
            # Query the database for entries with matching factual and rant tweets
            existing_entry = CombinedTweetResult.objects.filter(
                Q(factual_tweet=carbon_content) & 
                Q(rant_tweet=rant_content)
            ).first()

            if existing_entry:
                return True, {
                    'message': 'These tweets have already been used for generation',
                    'previous_result': {
                        'tweet': existing_entry.combined_tweet,
                        'sources': {
                            'carbon_tweet': existing_entry.factual_tweet,
                            'rant_tweet': existing_entry.rant_tweet
                        },
                        'safety_data': existing_entry.safety_score,
                        'popularity_data': existing_entry.popularity_score,
                        'extracted_urls': existing_entry.extracted_urls,
                        'created_at': existing_entry.created_at,
                        'status': 'duplicate'
                    }
                }
            return False, None
        except Exception as e:
            logging.error(f"Error checking for duplicate tweets: {str(e)}")
            return False, None

    def process_tweet_generation(self, carbon_content, rant_content):
        try:
            # First check if these tweets have been used before
            is_duplicate, duplicate_result = self.check_tweets_already_used(carbon_content, rant_content)
            if is_duplicate:
                return duplicate_result

            # Generate the tweet
            result = self.generator.generate_combined_tweet(carbon_content, rant_content)
            
            # Validate the generation result
            is_valid, validation_message = self.validate_generation_result(result)
            if not is_valid:
                logging.error(f"Tweet generation validation failed: {validation_message}")
                return {
                    'error': f"Tweet generation failed: {validation_message}",
                    'status': 'error'
                }

            # Extract and process data
            tweet_with_urls = result['tweet']
            all_source_urls = result['extracted_urls']
            safety_score = self.extract_safety_score(result['safety_data'])
            popularity_data = result['popularity_data']
            popularity_score = self.extract_popularity_score(popularity_data)

            # Validate processed data
            if not safety_score or not popularity_score:
                logging.error("Failed to extract safety or popularity scores")
                return {
                    'error': "Failed to process safety or popularity data",
                    'status': 'error'
                }

            # Only store in DB if all validations pass
            try:
                CombinedTweetResult.objects.create(
                    combined_tweet=tweet_with_urls,
                    factual_tweet=carbon_content,
                    rant_tweet=rant_content,
                    extracted_urls=all_source_urls,
                    popularity_score=popularity_score,
                    safety_score=safety_score
                )
            except Exception as db_error:
                logging.error(f"Database storage failed: {str(db_error)}")
                return {
                    'error': "Failed to store tweet in database",
                    'status': 'error'
                }

            return {
                'tweet': tweet_with_urls,
                'sources': {
                    'carbon_tweet': carbon_content,
                    'rant_tweet': rant_content
                },
                'safety_data': safety_score,
                'popularity_data': popularity_data,
                'extracted_urls': all_source_urls,
                'status': 'success'
            }

        except Exception as e:
            logging.error(f"Error in tweet generation process: {str(e)}")
            return {
                'error': f"An error occurred during tweet generation: {str(e)}",
                'status': 'error'
            }


# Create a single instance of the handler
tweet_handler = TweetViewHandler()

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
    carbon_content = entries['carbon_tweet']['content'] or ""
    rant_content = entries['rant_tweet']['content'] or ""
    result = tweet_handler.process_tweet_generation(carbon_content, rant_content)
    
    if result.get('status') == 'error':
        return Response(result, status=400)
    elif result.get('status') == 'duplicate':
        return Response(result, status=200)  # Return 200 for duplicate as it's not an error
    return Response(result)

@api_view(['POST'])
def generate_combined_post(request):
    data = request.data
    if 'carbon_tweet' not in data or 'rant_tweet' not in data:
        return Response({'error': 'Missing required tweet content (carbon_tweet and/or rant_tweet)'}, status=400)

    carbon_content = data['carbon_tweet'] or ""
    rant_content = data['rant_tweet'] or ""
    result = tweet_handler.process_tweet_generation(carbon_content, rant_content)
    
    if result.get('status') == 'error':
        return Response(result, status=400)
    elif result.get('status') == 'duplicate':
        return Response(result, status=200)  # Return 200 for duplicate as it's not an error
    return Response(result)

@api_view(['GET'])
def test(request):
    return Response({"message": "Test endpoint working"})

@api_view(['POST'])
def test_with_sample(request):
    data = request.data
    if 'carbon_tweet' not in data or 'rant_tweet' not in data:
        return Response({'error': 'Missing required sample tweets'}, status=400)

    try:
        tweet = tweet_handler.generator.generate_combined_tweet(data['carbon_tweet'], data['rant_tweet'])['tweet']
        
        # --- Force URL Appending for test_with_sample ---
        _, carbon_urls_test = tweet_handler.url_processor.extract_urls(data['carbon_tweet'])
        _, rant_urls_test = tweet_handler.url_processor.extract_urls(data['rant_tweet'])
        all_source_urls_test = carbon_urls_test + rant_urls_test

        tweet_with_urls_test = tweet

        if all_source_urls_test:
            first_url_test = all_source_urls_test[0]
            if tweet_with_urls_test and not tweet_with_urls_test.endswith(' '):
                tweet_with_urls_test += ' '
            tweet_with_urls_test += first_url_test

        return Response({
            'tweet': tweet_with_urls_test,
            'tweet_length': len(tweet_with_urls_test),
            'sources': {
                'carbon_tweet': data['carbon_tweet'],
                'rant_tweet': data['rant_tweet']
            },
            'status': 'success'
        })
    except Exception as e:
        logging.error(f"Error in test_with_sample: {str(e)}")
        return Response({
            'error': f"An error occurred during test: {str(e)}",
            'status': 'error'
        }, status=400)

