from flask import Flask, jsonify, request
import psycopg2
from datetime import datetime
import re
import requests
import sys
import os
from dotenv import load_dotenv
import logging
import json
from functools import wraps
import validators
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('carbonsustain')

# Add the project root to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm.openai_inference import TweetLLM
from utils.retry_logic import build_retry_prompt

class APILogger:
    """Class to handle API request and response logging"""
    
    @staticmethod
    def log_api_call(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Log the API call
            request_id = datetime.now().strftime('%Y%m%d%H%M%S%f')
            endpoint = request.path
            method = request.method
            ip = request.remote_addr
            
            logger.info(f"REQUEST [{request_id}] - {method} {endpoint} from {ip}")
            
            # Get request data for logging
            if request.is_json:
                logger.info(f"REQUEST DATA [{request_id}]: {json.dumps(request.get_json())}")
            elif request.form:
                logger.info(f"REQUEST FORM [{request_id}]: {request.form}")
            elif request.args:
                logger.info(f"REQUEST ARGS [{request_id}]: {request.args}")
                
            # Execute the original function
            start_time = datetime.now()
            response = f(*args, **kwargs)
            duration = (datetime.now() - start_time).total_seconds()
                
            # Log the response
            if isinstance(response, tuple):
                resp_body, status_code = response
            else:
                resp_body, status_code = response, 200
                
            log_resp = resp_body.get_json() if hasattr(resp_body, 'get_json') else str(resp_body)
            logger.info(f"RESPONSE [{request_id}] - {status_code} - {duration:.2f}s: {log_resp}")
            
            return response
        
        return decorated_function


class URLProcessor:
    """Class for managing URL operations"""
    
    @staticmethod
    def extract_urls(text):
        """Extract URLs from text and return the text without URLs and a list of URLs"""
        logger.info(f"URL EXTRACTION - ORIGINAL TEXT: {text}")
        
        if not text:
            logger.info("URL EXTRACTION - Empty text provided, returning empty results")
            return "", []
            
        # More permissive URL pattern that can catch more URL formats
        # This regex matches URLs with or without http/https prefix
        url_pattern = re.compile(r'(https?://[^\s\'"]+|www\.[^\s\'"]+)')
        urls = url_pattern.findall(text)
        
        if urls:
            logger.info(f"URL EXTRACTION - RAW URLS FOUND: {', '.join(urls)}")
        else:
            logger.info("URL EXTRACTION - No raw URLs found in text")
            
        text_without_urls = url_pattern.sub('', text).strip()
        logger.info(f"URL EXTRACTION - TEXT AFTER URL REMOVAL: {text_without_urls}")
        
        # Validate URLs and filter out malformed ones
        valid_urls = []
        for url in urls:
            try:
                # Clean up the URL - remove trailing punctuation that might have been captured
                original_url = url
                url = url.rstrip('.,;:!?)"\'')
                if original_url != url:
                    logger.info(f"URL EXTRACTION - Cleaned URL: {original_url} -> {url}")
                
                # Add http:// prefix if it's missing
                if url.startswith('www.') and not url.startswith('http'):
                    original_url = url
                    url = 'http://' + url
                    logger.info(f"URL EXTRACTION - Added HTTP prefix: {original_url} -> {url}")
                
                # Basic URL validation - be more permissive here
                parsed = urlparse(url)
                if parsed.netloc:  # Just check if there's a domain
                    valid_urls.append(url)
                    logger.info(f"URL EXTRACTION - Valid URL found: {url}")
                else:
                    logger.warning(f"URL EXTRACTION - Invalid URL structure rejected: {url}, parsed result: {parsed}")
            except Exception as e:
                logger.warning(f"URL EXTRACTION - URL validation error for '{url}': {str(e)}")
        
        logger.info(f"URL EXTRACTION - TOTAL VALID URLS: {len(valid_urls)}")
        if valid_urls:
            logger.info(f"URL EXTRACTION - VALID URLS: {', '.join(valid_urls)}")
            
        return text_without_urls, valid_urls
    
    @staticmethod
    def append_urls_to_text(text, urls, char_limit=1000):
        """Append URLs to text while respecting the character limit"""
        logger.info(f"URL APPEND - ORIGINAL TEXT: {text}")
        logger.info(f"URL APPEND - URLS TO APPEND: {', '.join(urls) if urls else 'None'}")
        
        if not urls:
            logger.info("URL APPEND - No URLs to append, returning original text")
            return text
            
        result_text = text.strip()
        logger.info(f"URL APPEND - TEXT AFTER STRIPPING: {result_text}")
        
        # Debug info
        logger.info(f"URL APPEND - Starting URL append process with {len(urls)} URLs")
        logger.info(f"URL APPEND - Base text before adding URLs (len {len(result_text)}): {result_text}")
        
        # Sort URLs by length (shortest first) to maximize inclusion
        sorted_urls = sorted(urls, key=len)
        logger.info(f"URL APPEND - URLs sorted by length: {', '.join(sorted_urls)}")
        
        for i, url in enumerate(sorted_urls):
            # Only add if it's a valid URL
            if validators.url(url):
                old_result = result_text
                result_text += " " + url
                logger.info(f"URL APPEND - Added URL #{i+1}: {url}")
                logger.info(f"URL APPEND - TEXT AFTER URL #{i+1}: {result_text}")
            else:
                logger.info(f"URL APPEND - Skipped URL #{i+1} (invalid): {url}")
                
        logger.info(f"URL APPEND - FINAL TEXT: {result_text}")
        logger.info(f"URL APPEND - Final text length: {len(result_text)}")
        return result_text


class ExternalAPIClient:
    """Class for making calls to external APIs"""
    
    @staticmethod
    def call_api(url, tweet):
        """Call external API and return status and detailed results"""
        try:
            # Log the full tweet before making the API call
            logger.info(f"TWEET BEFORE API CALL to {url.split('/')[-1] if url else 'unknown'}: {tweet}")
            
            logger.info(f"Calling external API: {url} with tweet: {tweet[:50]}...")
            response = requests.post(url, json={"text": tweet})
            response_data = response.json()
            
            # Log the response data (excluding large scores if present)
            log_data = response_data.copy() if isinstance(response_data, dict) else response_data
            if isinstance(log_data, dict) and "scores" in log_data:
                log_data["scores"] = "scores data present but not logged"
            logger.info(f"API RESPONSE from {url.split('/')[-1] if url else 'unknown'}: {json.dumps(log_data)}")
            
            # Check if this is the safety API response format
            if isinstance(response_data, dict) and "is_appropriate" in response_data:
                is_approved = response_data.get("is_appropriate", False)
                
                # Log detailed scores if available
                if "scores" in response_data:
                    scores = response_data["scores"]
                    logger.info(f"Safety API scores: {json.dumps(scores)}")
                    
                    # Find the highest offending category
                    if not is_approved and scores:
                        highest_category = max(scores.items(), key=lambda x: x[1])
                        logger.warning(f"Content rejected - highest toxicity category: {highest_category[0]} ({highest_category[1]:.4f})")
                
                status = "approved" if is_approved else "rejected"
                
                # Log the status and the original tweet
                logger.info(f"TWEET AFTER API CALL to {url.split('/')[-1] if url else 'unknown'} - STATUS: {status}: {tweet}")
                
                return status, response_data
                
            # Check if this is the popularity API response with predicted_score
            elif isinstance(response_data, dict) and "predicted_score" in response_data:
                score = response_data.get("predicted_score", 0)
                threshold = 5.0  # Assuming threshold for approval is 5.0
                logger.info(f"Popularity predicted score: {score:.2f} (threshold: {threshold})")
                
                status = "approved" if score >= threshold else "rejected"
                
                # Log the status and the original tweet
                logger.info(f"TWEET AFTER API CALL to {url.split('/')[-1] if url else 'unknown'} - STATUS: {status}: {tweet}")
                
                return status, response_data
                
            # Check if this is the popularity API response with simple score
            elif isinstance(response_data, dict) and "score" in response_data:
                score = response_data.get("score", 0)
                threshold = 0.6  # Assuming threshold for approval is 0.6
                logger.info(f"Popularity score: {score:.4f} (threshold: {threshold})")
                
                status = "approved" if score >= threshold else "rejected"
                
                # Log the status and the original tweet
                logger.info(f"TWEET AFTER API CALL to {url.split('/')[-1] if url else 'unknown'} - STATUS: {status}: {tweet}")
                
                return status, response_data
                
            # Fall back to the original simple response format
            else:
                status = response_data.get("status", "rejected")
                logger.info(f"External API response from {url}: {status}")
                
                # Log the status and the original tweet
                logger.info(f"TWEET AFTER API CALL to {url.split('/')[-1] if url else 'unknown'} - STATUS: {status}: {tweet}")
                
                return status, response_data
                
        except Exception as e:
            logger.error(f"Error calling external API {url}: {str(e)}")
            # Log the error with the original tweet
            logger.error(f"TWEET ERROR during API call to {url.split('/')[-1] if url else 'unknown'}: {tweet}")
            return "rejected", {"error": str(e)}


class DatabaseManager:
    """Class for database operations"""
    
    def __init__(self, config):
        self.config = config
        
    def get_connection(self):
        """Get a database connection"""
        return psycopg2.connect(**self.config)
    
    def get_latest_entries(self):
        """Get the latest carbon and rant tweets from the database"""
        try:
            logger.info("Connecting to database for latest entries")
            conn = self.get_connection()
            cur = conn.cursor()

            # Get latest content and image_urls from carbontruth_tweets
            cur.execute("SELECT content, image_urls FROM carbontruth_tweets ORDER BY created_at DESC LIMIT 1")
            carbon_row = cur.fetchone()
            carbon_content = carbon_row[0] if carbon_row else None
            carbon_images = carbon_row[1] if carbon_row else []

            # Get latest content from carbonrant_tweets
            cur.execute("SELECT content FROM carbonrant_tweets ORDER BY created_at DESC LIMIT 1")
            rant_row = cur.fetchone()
            rant_content = rant_row[0] if rant_row else None

            cur.close()
            conn.close()
            
            logger.info(f"Retrieved latest entries - Carbon content length: {len(carbon_content) if carbon_content else 0}, Rant content length: {len(rant_content) if rant_content else 0}")

            return {
                'carbon_tweet': {
                    'content': carbon_content,
                    'image_urls': carbon_images
                },
                'rant_tweet': {
                    'content': rant_content
                }
            }

        except Exception as e:
            logger.error(f"Error getting latest entries: {str(e)}")
            raise


class TweetGenerator:
    """Class for generating combined tweets"""
    
    def __init__(self, llm_model, safety_api_url, popularity_api_url, char_limit=1000):
        self.llm = llm_model
        self.safety_api = safety_api_url
        self.popularity_api = popularity_api_url
        self.char_limit = char_limit  # Setting a very high limit effectively removes it
        self.url_processor = URLProcessor()
        self.api_client = ExternalAPIClient()
        
    def generate_prompt(self, carbon_text, rant_text):
        """Create a prompt for the LLM to generate a combined tweet"""
        return f"""
        Combine these two climate-related tweets into a single coherent tweet:
        
        Tweet 1: {carbon_text}
        
        Tweet 2: {rant_text}
        
        Guidelines:
        1. Focus on creating substantive, fact-based content
        2. Merge key points from both tweets
        3. Keep the tone data-driven and action-oriented
        4. Include at most 2 relevant hashtags
        5. Do not add any URLs (they will be added automatically)
        """
    
    def generate_combined_tweet(self, carbon_content, rant_content):
        """Generate a combined tweet from carbon and rant content"""
        try:
            logger.info("Starting tweet combination process")
            
            # Extract URLs from both contents
            carbon_text, carbon_urls = self.url_processor.extract_urls(carbon_content)
            rant_text, rant_urls = self.url_processor.extract_urls(rant_content)
            all_urls = carbon_urls + rant_urls
            
            logger.info(f"Extracted URLs - Count: {len(all_urls)}")
            if all_urls:
                logger.info(f"URLs found: {', '.join(all_urls)}")

            # Create a prompt for the LLM
            prompt = self.generate_prompt(carbon_text, rant_text)

            # Generate combined tweet
            logger.info("Generating combined tweet with LLM")
            combined_tweet = self.llm.generate(prompt)
            logger.info(f"Generated combined tweet - Length: {len(combined_tweet)}")
            logger.info(f"Combined tweet content: {combined_tweet}")
            
            # Fix any trailing ellipsis or truncation markers that the LLM might have added
            combined_tweet = self._fix_truncation(combined_tweet)
            
            # Extract any new URLs that might have been generated and add them to our list
            combined_text, new_urls = self.url_processor.extract_urls(combined_tweet)
            all_urls = list(set(all_urls + new_urls))  # Remove duplicates
            
            logger.info(f"Final URL count after extraction: {len(all_urls)}")
            if all_urls:
                logger.info(f"URLs to append: {', '.join(all_urls)}")
            
            # Append URLs to the combined text
            combined_text = self.url_processor.append_urls_to_text(combined_text, all_urls, self.char_limit)
            logger.info(f"Final combined text with URLs: {combined_text}")
            
            # Perform a final validation check on the combined text
            if not combined_text or combined_text.isspace() or len(combined_text) < 20:
                logger.warning("Generated tweet is too short or empty - generating fallback content")
                combined_text = "Our fight for renewable energy is also a fight for ecosystems. Every sustainable choice helps protect our planet. #ClimateAction #RenewableEnergy"
                # Try to add URLs to the fallback content too
                if all_urls:
                    combined_text = self.url_processor.append_urls_to_text(combined_text, all_urls, self.char_limit)

            # Check against safety and popularity APIs
            combined_text = self.validate_and_improve_tweet(combined_text, all_urls)

            return combined_text
            
        except Exception as e:
            logger.error(f"Error generating combined tweet: {str(e)}")
            raise
    
    def validate_and_improve_tweet(self, tweet_text, urls=None):
        """Validate the tweet against safety and popularity APIs and improve if needed"""
        urls = urls or []
        
        # Store the original number of URLs for verification
        original_url_count = len(urls)
        logger.info(f"Starting API validation with {original_url_count} URLs")
        logger.info(f"TWEET BEFORE VALIDATION: {tweet_text}")
        
        # Check against safety API
        logger.info("Checking tweet against safety API")
        safety_status, safety_data = self.api_client.call_api(self.safety_api, tweet_text)
        logger.info(f"Safety check result: {safety_status}")
        
        # Retry if safety check failed with specific information about why
        if safety_status != "approved":
            reason = "safety"
            if isinstance(safety_data, dict) and "scores" in safety_data:
                scores = safety_data["scores"]
                highest_category = max(scores.items(), key=lambda x: x[1])
                category, score = highest_category
                if score > 0.8:  # Only use specific category if score is significant
                    reason = f"safety - high {category} score"
            
            logger.info(f"Tweet rejected by safety API ({reason}) - Retrying...")
            retry_prompt = build_retry_prompt(reason, tweet_text)
            logger.info(f"RETRY PROMPT FOR SAFETY: {retry_prompt}")
            
            # Extract the URLs from the current tweet before generating a new one
            tweet_without_urls, more_urls = self.url_processor.extract_urls(tweet_text)
            if more_urls:
                logger.info(f"Found {len(more_urls)} URLs in current tweet before safety regeneration")
                urls = list(set(urls + more_urls))  # Add any new URLs to our list
                
            # Generate new tweet
            new_tweet_text = self.llm.generate(retry_prompt)
            logger.info(f"Generated new tweet after safety rejection - Length: {len(new_tweet_text)}")
            logger.info(f"TWEET AFTER SAFETY REJECTION: {new_tweet_text}")
            
            # Extract any URLs that might have been generated in the new tweet
            new_text_without_urls, new_text_urls = self.url_processor.extract_urls(new_tweet_text)
            if new_text_urls:
                logger.info(f"Found {len(new_text_urls)} URLs in regenerated tweet after safety check")
                urls = list(set(urls + new_text_urls))  # Add any new URLs to our list
                
            # Use the text without URLs for further processing
            tweet_text = new_text_without_urls
            logger.info(f"TWEET AFTER SAFETY URL EXTRACTION: {tweet_text}")
            
            # Check safety again for logging but don't retry again
            new_safety_status, new_safety_data = self.api_client.call_api(self.safety_api, tweet_text)
            if new_safety_status != "approved":
                logger.warning("Retried tweet still fails safety check, but proceeding")
        
        # Now check popularity
        logger.info("Checking tweet against popularity API")
        popularity_status, popularity_data = self.api_client.call_api(self.popularity_api, tweet_text)
        logger.info(f"Popularity check result: {popularity_status}")
        
        # Retry if popularity check failed
        if popularity_status != "approved":
            reason = "popularity"
            if isinstance(popularity_data, dict):
                if "predicted_score" in popularity_data:
                    score = popularity_data["predicted_score"]
                    reason = f"popularity - low engagement score ({score:.2f}/10)"
                elif "score" in popularity_data:
                    score = popularity_data["score"]
                    reason = f"popularity - low engagement score ({score:.2f})"
                
            logger.info(f"Tweet rejected by popularity API ({reason}) - Retrying...")
            retry_prompt = build_retry_prompt(reason, tweet_text)
            logger.info(f"RETRY PROMPT FOR POPULARITY: {retry_prompt}")
            
            # Extract the URLs from the current tweet before generating a new one
            tweet_without_urls, more_urls = self.url_processor.extract_urls(tweet_text)
            if more_urls:
                logger.info(f"Found {len(more_urls)} URLs in current tweet before popularity regeneration")
                urls = list(set(urls + more_urls))  # Add any new URLs to our list
                
            # Generate new tweet
            new_tweet_text = self.llm.generate(retry_prompt)
            logger.info(f"Generated new tweet after popularity rejection - Length: {len(new_tweet_text)}")
            logger.info(f"TWEET AFTER POPULARITY REJECTION: {new_tweet_text}")
            
            # Extract any URLs that might have been generated in the new tweet
            new_text_without_urls, new_text_urls = self.url_processor.extract_urls(new_tweet_text)
            if new_text_urls:
                logger.info(f"Found {len(new_text_urls)} URLs in regenerated tweet after popularity check")
                urls = list(set(urls + new_text_urls))  # Add any new URLs to our list
                
            # Use the text without URLs for further processing
            tweet_text = new_text_without_urls
            logger.info(f"TWEET AFTER POPULARITY URL EXTRACTION: {tweet_text}")

        # Always re-append URLs at the end
        if urls:
            logger.info(f"Re-appending {len(urls)} URLs to final tweet")
            logger.info(f"TWEET BEFORE FINAL URL APPEND: {tweet_text}")
            logger.info(f"URLS TO APPEND: {', '.join(urls)}")
            tweet_text = self.url_processor.append_urls_to_text(tweet_text, urls, self.char_limit)
            logger.info(f"TWEET AFTER FINAL URL APPEND: {tweet_text}")
            
        # Verify URLs were added
        _, final_urls = self.url_processor.extract_urls(tweet_text)
        logger.info(f"Final URL count: {len(final_urls)} (started with {original_url_count})")
        if len(final_urls) < len(urls):
            logger.warning(f"Some URLs could not be appended. Started with {len(urls)}, ended with {len(final_urls)}")
            logger.warning(f"Missing URLs: {', '.join(set(urls) - set(final_urls))}")
        
        logger.info(f"FINAL VALIDATED TWEET: {tweet_text}")
        return tweet_text

    def _fix_truncation(self, text):
        """Fix any truncation in text by removing common truncation markers"""
        if not text:
            return text
        
        # Remove trailing ellipsis and similar markers that might indicate truncation
        cleaned_text = re.sub(r'(?:\s*\.{3,}|\s*…|\s*\[…\]|\s*\[\.\.\.\]|\s*etc\.?|\s*-+|\s*_+)$', '', text)
        
        # Log if changes were made
        if cleaned_text != text:
            logger.info(f"Fixed truncation markers: '{text}' -> '{cleaned_text}'")
            
        return cleaned_text.strip()


class CarbonSustainAPI:
    """Main application class"""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Initialize Flask application
        self.app = Flask(__name__)
        
        # Configure Flask for handling large JSON responses without truncation
        self.app.config['JSON_SORT_KEYS'] = False  # Preserve order of keys
        self.app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False  # Disable pretty printing
        self.app.json.compact = True  # Use compact JSON representation
        
        # Safety and popularity API endpoints
        self.safety_api = os.getenv('SAFETY_API_URL')
        self.popularity_api = os.getenv('POPULARITY_API_URL')
        
        # Database configuration
        self.db_config = {
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT'),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD')
        }
        
        # Initialize components
        self.db_manager = DatabaseManager(self.db_config)
        try:
            self.llm = TweetLLM(model_path="../llm/finetuned-twitter-llm1")
            logger.info("LLM model initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing LLM model: {str(e)}")
            # Create a fallback "dummy" LLM for testing
            self.llm = self._create_dummy_llm()
            
        # Initialize tweet generator with no character limit
        self.tweet_generator = TweetGenerator(self.llm, self.safety_api, self.popularity_api, char_limit=1000)
        
        # Set up routes
        self.setup_routes()
    
    def _create_dummy_llm(self):
        """Create a dummy LLM object for testing when the real model can't be loaded"""
        class DummyLLM:
            def generate(self, prompt):
                logger.warning("Using dummy LLM implementation")
                return "Climate change requires immediate action. Renewable energy and carbon reduction are essential for a sustainable future. #ClimateAction #Sustainability"
        return DummyLLM()
    
    def setup_routes(self):
        """Set up the Flask routes"""
        # Home endpoint
        @self.app.route('/')
        @APILogger.log_api_call
        def home():
            return jsonify({"message": "CarbonSustain API is working"})
        
        # Latest entry endpoint
        @self.app.route('/latest-entry')
        @APILogger.log_api_call
        def get_latest_entry():
            try:
                entries = self.db_manager.get_latest_entries()
                return jsonify(entries)
            except Exception as e:
                logger.error(f"Error in get_latest_entry: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        # Generate combined tweet endpoint
        @self.app.route('/generate-combined', methods=['GET'])
        @APILogger.log_api_call
        def generate_combined():
            try:
                entries = self.db_manager.get_latest_entries()
                carbon_content = entries['carbon_tweet']['content'] or ""
                rant_content = entries['rant_tweet']['content'] or ""
                
                combined_text = self.tweet_generator.generate_combined_tweet(carbon_content, rant_content)
                
                logger.info("Tweet generation process completed successfully")
                logger.info(f"Final tweet length: {len(combined_text)}")
                logger.info(f"Final tweet content: {combined_text}")
                
                response_data = {
                    'tweet': combined_text,
                    'tweet_length': len(combined_text),
                    'sources': {
                        'carbon_tweet': carbon_content,
                        'rant_tweet': rant_content
                    }
                }
                
                # Use Flask's direct Response object for more control
                return jsonify(response_data)
            except Exception as e:
                logger.error(f"Error in generate_combined: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        # Test endpoint
        @self.app.route('/test')
        @APILogger.log_api_call
        def test():
            return jsonify({"message": "Test endpoint working"})
        
        # Test with sample tweet endpoint
        @self.app.route('/test-with-sample', methods=['POST'])
        @APILogger.log_api_call
        def test_with_sample():
            try:
                # Get sample tweets from request
                data = request.get_json()
                if not data or 'carbon_tweet' not in data or 'rant_tweet' not in data:
                    return jsonify({'error': 'Missing required sample tweets'}), 400
                    
                carbon_content = data.get('carbon_tweet', '')
                rant_content = data.get('rant_tweet', '')
                
                logger.info(f"Testing with sample tweets - Carbon length: {len(carbon_content)}, Rant length: {len(rant_content)}")
                
                combined_text = self.tweet_generator.generate_combined_tweet(carbon_content, rant_content)
                
                logger.info("Tweet generation from samples completed successfully")
                logger.info(f"Final sample tweet length: {len(combined_text)}")
                logger.info(f"Final sample tweet content: {combined_text}")
                
                response_data = {
                    'tweet': combined_text,
                    'tweet_length': len(combined_text),
                    'sources': {
                        'carbon_tweet': carbon_content,
                        'rant_tweet': rant_content
                    }
                }
                
                # Use Flask's direct Response object for more control
                return jsonify(response_data)
            except Exception as e:
                logger.error(f"Error in test_with_sample: {str(e)}")
                return jsonify({'error': str(e)}), 500
    
    def run(self, debug=True, port=5000):
        """Run the Flask application"""
        logger.info("Starting CarbonSustain DB API")
        self.app.run(debug=debug, port=port)


# Create and run the application when executed directly
if __name__ == '__main__':
    api = CarbonSustainAPI()
    api.run(debug=True, port=5000)
