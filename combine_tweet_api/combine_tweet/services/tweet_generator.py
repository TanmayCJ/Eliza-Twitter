import re
from django.conf import settings
from combine_tweet.services.url_processor import URLProcessor
from combine_tweet.services.external_api import ExternalAPIClient
from combine_tweet.services.retry_logic import build_retry_prompt
from combine_tweet.services.openai_inference import TweetLLM
import json
import os
import logging

with open(os.path.join(settings.BASE_DIR, 'combine_tweet', 'character3.json')) as f:
    CHARACTER = json.load(f)

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
        self.fact_weight = 0.9  # default 70% facts
        self.rant_weight = 0.1  # default 30% rant

    def set_blend_ratio(self, fact_weight, rant_weight):
        if not abs((fact_weight + rant_weight) - 1.0) < 0.01:
            raise ValueError("Blend weights must add up to 1.0")
        self.fact_weight = fact_weight
        self.rant_weight = rant_weight

    def generate_prompt(self, carbon_text, rant_text):
        primary_tone = ', '.join(CHARACTER['tone']['primary'])
        secondary_tone = ', '.join(CHARACTER['tone']['secondary'])

        fact_length = int(len(carbon_text) * self.fact_weight)
        rant_length = int(len(rant_text) * self.rant_weight)

        fact_part = carbon_text.strip()[:fact_length]
        rant_part = rant_text.strip()[:rant_length]

        return f"""
You are {CHARACTER['persona_name']} — {CHARACTER['persona_description']}.
Use a {primary_tone} tone for the facts.
Use a {secondary_tone} tone for the emotional parts.
Merge the following contents respecting the blend:
- FACTUAL (about {self.fact_weight * 100:.0f}%): {fact_part}
- EMOTIONAL (about {self.rant_weight * 100:.0f}%): {rant_part}
Now write the tweet:
"""

    def generate_combined_tweet(self, carbon_content, rant_content):
        carbon_text, carbon_urls = self.url_processor.extract_urls(carbon_content)
        rant_text, rant_urls = self.url_processor.extract_urls(rant_content)
        all_urls = carbon_urls + rant_urls

        # Check if tweets are related
        are_related = self.llm.check_tweet_relatedness(carbon_text, rant_text)
        
        # If tweets are not related, use only the carbon tweet
        print("are_related",are_related)
        if not are_related:
            primary_tone = ', '.join(CHARACTER['tone']['primary'])
            secondary_tone = ', '.join(CHARACTER['tone']['secondary'])
            
            prompt = f"""
            You are {CHARACTER['persona_name']} — {CHARACTER['persona_description']}.
            Use a {primary_tone} tone for about 70% of the content.
            Use a {secondary_tone} tone for about 30% of the content.
            
            Create a tweet based solely on this content:
            {carbon_text}
            
            Maintain the factual accuracy and make it coherentwhile making it engaging.
            """
        else:
            # If related, use the normal blending approach
            prompt = self.generate_prompt(carbon_text, rant_text)
        
        try:
            combined = self.llm.generate(prompt)
            combined = self._fix_truncation(combined)

            text, new_urls = self.url_processor.extract_urls(combined)
            all_urls = list(set(all_urls + new_urls))
            text = self.url_processor.append_urls_to_text(text, all_urls, self.char_limit)

            if not text or len(text) < 20:
                text = "Our fight for renewable energy is also a fight for ecosystems. Every sustainable choice helps protect our planet. #ClimateAction #RenewableEnergy"
                if all_urls:
                    text = self.url_processor.append_urls_to_text(text, all_urls, self.char_limit)

            #validated = self.validate_and_improve_tweet(text, all_urls)
            validated = None
            return validated if validated is not None else text
        except Exception as e:
            logging.error("Error generating combined tweet: %s", str(e))
            return "An error occurred while generating the tweet. Please try again."

    def validate_and_improve_tweet(self, tweet_text, urls=None):
        urls = urls or []
        safety_status, safety_data = self.api_client.call_api(self.safety_api, tweet_text)
        retries = 0
        while safety_status != 'approved' and retries < self.max_retries:
            retries += 1
            reason = 'safety'
            if isinstance(safety_data, dict) and 'scores' in safety_data:
                cat, score = max(safety_data['scores'].items(), key=lambda x: x[1])
                if score > 0.8:
                    reason = f'safety - high {cat} score'
            retry_prompt = build_retry_prompt(reason, tweet_text)
            new_text = self.llm.generate(retry_prompt)
            tweet_text, more_urls = self.url_processor.extract_urls(new_text)
            urls = list(set(urls + more_urls))
            safety_status, safety_data = self.api_client.call_api(self.safety_api, tweet_text)
        if safety_status != 'approved' and not self.proceed_regardless:
            return None

        popularity_status, popularity_data = self.api_client.call_api(self.popularity_api, tweet_text)
        retries = 0
        while popularity_status != 'approved' and retries < self.max_retries:
            retries += 1
            reason = 'popularity'
            if isinstance(popularity_data, dict) and 'predicted_score' in popularity_data:
                reason = f"popularity - low engagement score ({popularity_data['predicted_score']:.2f}/10)"
            elif isinstance(popularity_data, dict) and 'score' in popularity_data:
                reason = f"popularity - low engagement score ({popularity_data['score']:.2f})"
            retry_prompt = build_retry_prompt(reason, tweet_text)
            new_text = self.llm.generate(retry_prompt)
            tweet_text, more_urls = self.url_processor.extract_urls(new_text)
            urls = list(set(urls + more_urls))
            popularity_status, popularity_data = self.api_client.call_api(self.popularity_api, tweet_text)
        if popularity_status != 'approved' and not self.proceed_regardless:
            return None

        if urls:
            tweet_text = self.url_processor.append_urls_to_text(tweet_text, urls, self.char_limit)

        return tweet_text

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
