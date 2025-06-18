import re
from django.conf import settings
from combine_tweet.services.url_processor import URLProcessor
from combine_tweet.services.external_api import ExternalAPIClient
from combine_tweet.services.retry_logic import build_retry_prompt
from combine_tweet.services.openai_inference import TweetLLM
import json
import os
import logging



class TweetGenerator:
    def __init__(self):
        self.llm = TweetLLM()
        self.safety_api = settings.SAFETY_API_URL
        self.popularity_api = settings.POPULARITY_API_URL
        self.char_limit = 1000
        self.max_retries = settings.MAX_API_RETRIES
        self.proceed_regardless = settings.PROCEED_REGARDLESS
        self.url_processor = URLProcessor()
        self.api_client = ExternalAPIClient()

        # Blend ratios
        self.fact_weight = 0.7  
        self.rant_weight = 0.3  

    def set_blend_ratio(self, fact_weight, rant_weight):
        if not abs((fact_weight + rant_weight) - 1.0) < 0.01:
            raise ValueError("Blend weights must add up to 1.0")
        self.fact_weight = fact_weight
        self.rant_weight = rant_weight

    def generate_combined_tweet(self, carbon_content, rant_content):
        carbon_text, carbon_urls = self.url_processor.extract_urls(carbon_content)
        rant_text, rant_urls = self.url_processor.extract_urls(rant_content)
        all_urls = carbon_urls + rant_urls
        try:
            combined = self.llm.generate(carbon_text, rant_text)
            combined = self._fix_truncation(combined)

            text, new_urls = self.url_processor.extract_urls(combined)
            all_urls = list(set(all_urls + new_urls))
            text = self.url_processor.append_urls_to_text(text, all_urls, self.char_limit)

            if not text or len(text) < 20:
                text = "Our fight for renewable energy is also a fight for ecosystems. Every sustainable choice helps protect our planet. #ClimateAction #RenewableEnergy"
                if all_urls:
                    text = self.url_processor.append_urls_to_text(text, all_urls, self.char_limit)

            validated, safety_data, popularity_data = self.validate_and_improve_tweet(text, all_urls)
            final_tweet = validated if validated is not None else text
            return {
                'tweet': final_tweet,
                'extracted_urls': all_urls,
                'safety_data': safety_data,
                'popularity_data': popularity_data
            }
        except Exception as e:
            logging.error("Error generating combined tweet: %s", str(e))
            return {
                'tweet': "An error occurred while generating the tweet. Please try again.",
                'extracted_urls': all_urls,
                'safety_data': {'error': str(e)},
                'popularity_data': {'error': str(e)}
            }

    def validate_and_improve_tweet(self, tweet_text, urls=None):
        text = tweet_text
        urls = urls or []
        safety_status, safety_data = self.api_client.call_api(self.safety_api, tweet_text)
        is_appropriate = self._extract_safety_appropriate(safety_data)
        print("safety_data", safety_data)
        print("is_appropriate", is_appropriate)
        if is_appropriate:
            safety_status = 'approved'
        else:
            safety_status = 'not_approved'
        retries = 0
        while safety_status != 'approved' and retries < self.max_retries:
            retries += 1
            reason = 'safety'
            retry_prompt = build_retry_prompt(reason, tweet_text)
            new_text = self.llm.generate_from_prompt(retry_prompt)
            tweet_text, more_urls = self.url_processor.extract_urls(new_text)
            urls = list(set(urls + more_urls))
            safety_status, safety_data = self.api_client.call_api(self.safety_api, tweet_text)
            is_appropriate = self._extract_safety_appropriate(safety_data)
            if is_appropriate:
                safety_status = 'approved'
            else:
                safety_status = 'not_approved'
        if safety_status != 'approved' and not self.proceed_regardless:
            return None, safety_data, None
        
        print(tweet_text)
        popularity_status, popularity_data = self.api_client.call_api(self.popularity_api, tweet_text)
        score = self._extract_popularity_score(popularity_data)
        if score is not None and score < 30:
            popularity_status = 'not_approved'
        else:
            popularity_status = 'approved'
        retries = 2
        print("popularity_status", popularity_status,"score", score)
        while popularity_status != 'approved' and retries < self.max_retries:
            retries += 1
            reason = 'popularity'
            score = self._extract_popularity_score(popularity_data)
            if score is not None:
                reason = f"popularity - low engagement score ({score:.2f})"
            retry_prompt = build_retry_prompt(reason, tweet_text)
            new_text = self.llm.generate_from_prompt(retry_prompt)
            tweet_text, more_urls = self.url_processor.extract_urls(new_text)
            urls = list(set(urls + more_urls))
            popularity_status, popularity_data = self.api_client.call_api(self.popularity_api, tweet_text)
            print("popularity_data", popularity_data)
            score = self._extract_popularity_score(popularity_data)
            if score is not None and score < 30:
                popularity_status = 'not_approved'
            else:
                popularity_status = 'approved'
        if popularity_status != 'approved' and not self.proceed_regardless:
            return None, safety_data, popularity_data

        print("tweet_text", tweet_text)
        if urls:
            text = self.url_processor.append_urls_to_text(tweet_text, urls, self.char_limit)

        return tweet_text, safety_data, popularity_data

    def _extract_safety_appropriate(self, safety_data):
        if (
            isinstance(safety_data, dict)
            and 'text_safety_score' in safety_data
            and isinstance(safety_data['text_safety_score'], dict)
            and 'is_appropriate' in safety_data['text_safety_score']
        ):
            return bool(safety_data['text_safety_score']['is_appropriate'])
        return False

    def _extract_popularity_score(self, popularity_data):
        if isinstance(popularity_data, dict):
            if 'predicted_score' in popularity_data:
                return popularity_data['predicted_score']
            if 'score' in popularity_data:
                return popularity_data['score']
        return None

    def _fix_truncation(self, text):
        if not text:
            return text
        text = re.sub(r'^Tweet:\s*', '', text)
        text = re.sub(r'#(\w+\s+\w+)', r'#\1', text)
        text = re.sub(r'https?://\S+', '', text).strip()
        text = re.sub(r'\s+', ' ', text).strip()
        hashtags = re.findall(r'#\w+', text)
        if len(hashtags) > 3:
            for tag in hashtags[3:]:
                text = text.replace(tag, '')
        text = re.sub(
            r'(?:\s*\.{3,}|\s*…|\s*\[…\]|\s*\[\.\.\.\]|\s*etc\.?|\s*-+|\s*_+)$',
            '', text
        )
        return text.strip()
