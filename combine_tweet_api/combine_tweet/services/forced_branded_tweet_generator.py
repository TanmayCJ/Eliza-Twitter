import re
import os
import json
from django.conf import settings
from combine_tweet.services.url_processor import URLProcessor
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

with open(os.path.join(settings.BASE_DIR, 'combine_tweet', 'character3.json')) as f:
    CHARACTER = json.load(f)

# Configure the Gemini API client
client = genai.Client(api_key=os.getenv("YOUR_API_KEY"))

# Safety settings
safety_settings = [
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=types.HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=types.HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=types.HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=types.HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    ),
]

# System instruction
system_instruction = "You are a social media expert creating branded sustainability tweets"

class ForcedBrandedTweetGenerator:
    """
    Tweet generator that always includes the company name in every tweet,
    regardless of content suitability.
    """
    def __init__(self):
        self.brand_name = CHARACTER['persona_name']
        self.char_limit = 240
        self.url_processor = URLProcessor()
        
        # Dictionary of sustainability topics
        self.sustainability_topics = {
            "renewable_energy": ["solar", "wind", "renewable", "clean energy"],
            "climate_policy": ["carbon pricing", "emissions", "climate policy"],
            "biodiversity": ["species", "ecosystem", "wildlife", "habitat"],
            "sustainable_agriculture": ["farming", "agriculture", "food systems"],
            "clean_transport": ["electric vehicle", "ev", "transportation"],
            "circular_economy": ["recycling", "waste", "circular", "plastic"],
            "water": ["ocean", "marine", "water", "drought", "flood"],
            "climate_justice": ["equity", "communities", "frontline", "transition"],
            "green_tech": ["innovation", "technology", "cleantech"]
        }

    def generate_prompt(self, fact_text, context_text):
        """Generate a prompt that guarantees brand integration"""
        
        # Clean inputs
        fact_part = re.sub(r'^[0-9]+/\s*', '', fact_text).strip()
        context_part = re.sub(r'^(WAKE-UP CALL:)\s*', '', context_text).strip()
        
        # Identify sustainability topics in content
        identified_topics = []
        combined_text = (fact_part + " " + context_part).lower()
        
        for topic, keywords in self.sustainability_topics.items():
            for keyword in keywords:
                if keyword.lower() in combined_text:
                    topic_name = topic.replace("_", " ").title()
                    if topic_name not in identified_topics:
                        identified_topics.append(topic_name)
        
        # Default topics if none found
        if not identified_topics:
            identified_topics = ["Climate Action", "Sustainability"]
        
        # Extract statistics patterns
        money_pattern = r'(\$\d+(?:\.\d+)?(?:/[a-zA-Z]+)?|\d+(?:\.\d+)?[TMB])'
        percentage_pattern = r'(\d+(?:\.\d+)?%)'
        number_pattern = r'(\d+(?:\.\d+)?\s+(?:times|percent|degrees|tons|million|billion))'
        
        money_values = re.findall(money_pattern, fact_part + " " + context_part)
        percentages = re.findall(percentage_pattern, fact_part + " " + context_part)
        numbers = re.findall(number_pattern, fact_part + " " + context_part, re.IGNORECASE)
        
        all_stats = money_values + percentages + numbers
        
        # Generate relevant hashtags
        hashtags = []
        for topic in identified_topics[:2]:  # Use up to 2 topics
            clean_topic = topic.replace(" ", "")
            hashtags.append(f"#{clean_topic}")
        
        # Create the prompt with stronger emphasis on brand name integration without "Voice"
        return f"""
Create a branded tweet that naturally includes "{self.brand_name}" based on these inputs:

1. FACT: {fact_part}
2. CONTEXT: {context_part}

STRICT RULES:
1. MUST include "{self.brand_name}" exactly as written - no extra words or modifications
2. FORBIDDEN TO USE: "{self.brand_name} Voice" - never add "Voice" or any suffix to the brand name
3. DO NOT refer to the brand as "the {self.brand_name}"
4. Use either "we"/"our" or "{self.brand_name}" (without any suffix) to integrate the brand
5. Present {self.brand_name} as an active, leading organization taking action on sustainability

FORMAT REQUIREMENTS:
1. Include a specific statistic or data point for credibility 
2. Use 1-2 relevant hashtags from: {', '.join(hashtags)}
3. Keep tweet under 240 characters
4. Make the brand mention sound natural and integrated into the message

RELATED TOPICS: {', '.join(identified_topics)}
KEY STATISTICS: {', '.join(all_stats) if all_stats else "Extract key numbers from the content"}

Write a concise, data-driven tweet with seamless brand integration:
"""

    def generate_tweet(self, fact_content, context_content):
        """Generate a tweet that always includes brand integration"""
        
        # Extract URLs from content
        fact_text, fact_urls = self.url_processor.extract_urls(fact_content)
        context_text, context_urls = self.url_processor.extract_urls(context_content)
        all_urls = fact_urls + context_urls
        
        # Generate prompt
        prompt = self.generate_prompt(fact_text, context_text)
        
        try:
            # Format messages for Gemini with stronger emphasis on avoiding "Voice"
            messages = [
                {
                    "role": "system",
                    "content": (
                        f"You are a pro-sustainability climate advocate writing for {self.brand_name}.\n\n"
                        f"CRITICAL INSTRUCTION: ALWAYS include \"{self.brand_name}\" in every tweet EXACTLY as written.\n"
                        f"SERIOUS ERROR TO AVOID: NEVER add the word \"Voice\" or ANY suffix after {self.brand_name}.\n"
                        f"CORRECT USAGE: \"{self.brand_name}\" or \"we\" or \"our\"\n"
                        f"INCORRECT USAGE: \"{self.brand_name} Voice\", \"{self.brand_name}Voice\", \"the {self.brand_name}\"\n\n"
                        f"You are creating concise, data-driven branded tweets with seamless brand integration."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            formatted_prompt = "\n\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in messages])
            
            # Generate content
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=formatted_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    top_p=0.95,
                    top_k=64,
                    max_output_tokens=100,
                    system_instruction=f"Write tweets for {self.brand_name} without ever adding 'Voice' after the brand name.",
                    safety_settings=safety_settings,
                    response_mime_type="text/plain"
                )
            )
            
            # Process response
            tweet = response.text
            
            # Always check for Voice and remove it, regardless of whether it seems present
            tweet = self._remove_voice_suffix(tweet)
            
            # Double-check if Voice is still present in any form
            if "voice" in tweet.lower():
                tweet = self._remove_voice_suffix(tweet)  # Run again
                
                # If still present, remove the sentence containing both brand and voice
                if "voice" in tweet.lower() and self.brand_name.lower() in tweet.lower():
                    sentences = re.split(r'(?<=[.!?])\s+', tweet)
                    tweet = ' '.join([s for s in sentences if not ("voice" in s.lower() and self.brand_name.lower() in s.lower())])
                    
                    # If tweet is now empty, force brand integration
                    if not tweet.strip():
                        tweet = self._create_fallback_tweet(fact_text, context_text)
            
            # Ensure brand name is included
            if self.brand_name not in tweet and "we" not in tweet.lower() and "our" not in tweet.lower():
                tweet = self._force_brand_integration(tweet)
            
            # Clean up formatting
            tweet = self._fix_formatting(tweet)
            
            # Process URLs
            tweet_text, new_urls = self.url_processor.extract_urls(tweet)
            all_urls = list(set(all_urls + new_urls))
            final_tweet = self.url_processor.append_urls_to_text(tweet_text, all_urls, self.char_limit)
            
            return final_tweet
            
        except Exception as e:
            print(f"Error generating forced branded tweet: {str(e)}")
            return self._create_fallback_tweet(fact_text, context_text, all_urls)
    
    def _force_brand_integration(self, tweet):
        """Force brand integration if not present"""
        brand_name = self.brand_name
        
        # If tweet doesn't have brand name, add it at beginning or end
        if len(tweet) < 200:  # Room to add
            if tweet.startswith(("The ", "A ", "In ", "On ")):
                # Add brand name as actor
                return f"{brand_name} reports: {tweet}"
            else:
                # Add brand attribution at end
                return f"{tweet} - {brand_name}"
        else:
            # Replace first sentence with brand attribution
            sentences = re.split(r'(?<=[.!?])\s+', tweet)
            if len(sentences) > 1:
                return f"{brand_name} reveals: {' '.join(sentences[1:])}"
            else:
                # Truncate and add brand
                shortened = tweet[:180].rsplit(' ', 1)[0]
                return f"{shortened}. {brand_name} is taking action."
    
    def _remove_voice_suffix(self, text):
        """Remove any instance of 'Voice' after the brand name"""
        brand_name = self.brand_name
        
        # More aggressive pattern matching for 'Voice' removal 
        # First, handle case-insensitive "voice" removal 
        voice_variations = ["Voice", "voice", "VOICE", "VoIcE"]
        for variation in voice_variations:
            text = text.replace(f"{brand_name} {variation}", brand_name)
            text = text.replace(f"{brand_name}{variation}", brand_name)
            text = text.replace(f"{brand_name}'s {variation}", brand_name)
            text = text.replace(f"{brand_name}' {variation}", brand_name)
            text = text.replace(f"{brand_name}s {variation}", brand_name)
            text = text.replace(f"the {brand_name} {variation}", f"the {brand_name}")
            text = text.replace(f"from {brand_name} {variation}", f"from {brand_name}")
            text = text.replace(f"at {brand_name} {variation}", f"at {brand_name}")
        
        # Use regex for other patterns with word boundaries
        text = re.sub(rf'{re.escape(brand_name)}\s+[Vv][Oo][Ii][Cc][Ee]', brand_name, text)
        text = re.sub(rf'{re.escape(brand_name)}[Vv][Oo][Ii][Cc][Ee]', brand_name, text)
        text = re.sub(rf'[Aa][Tt]\s+{re.escape(brand_name)}\s+[Vv][Oo][Ii][Cc][Ee]', f"At {brand_name}", text)
        text = re.sub(rf'[Ff][Rr][Oo][Mm]\s+{re.escape(brand_name)}\s+[Vv][Oo][Ii][Cc][Ee]', f"From {brand_name}", text)
        text = re.sub(rf'[Tt][Hh][Ee]\s+{re.escape(brand_name)}\s+[Vv][Oo][Ii][Cc][Ee]', f"The {brand_name}", text)
        
        # One final check for any other voice mentions
        if "voice" in text.lower() and brand_name.lower() in text.lower():
            # Try to remove any remaining instances by finding the sentence with both
            sentences = re.split(r'(?<=[.!?])\s+', text)
            new_sentences = []
            for sentence in sentences:
                if "voice" in sentence.lower() and brand_name.lower() in sentence.lower():
                    # Remove the whole voice reference
                    sentence = re.sub(r'\b[Vv][Oo][Ii][Cc][Ee]\b', '', sentence)
                    # Clean up any double spaces
                    sentence = re.sub(r'\s+', ' ', sentence).strip()
                new_sentences.append(sentence)
            text = ' '.join(new_sentences)
        
        return text
    
    def _fix_formatting(self, text):
        """Clean up the generated tweet text"""
        if not text:
            return text
            
        # Remove prefixes
        text = re.sub(r'^(Tweet:|Here\'s the tweet:|Branded tweet:)\s*', '', text, flags=re.IGNORECASE)
        
        # Fix hashtags
        text = re.sub(r'#(\w+\s+\w+)', r'#\1', text)
        text = re.sub(r'(\w)#', r'\1 #', text)
        
        # Remove duplicate spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Limit hashtags to 2
        hashtags = re.findall(r'#\w+', text)
        if len(hashtags) > 2:
            for tag in hashtags[2:]:
                text = text.replace(tag, '')
                
        # Remove trailing ellipses
        text = re.sub(r'(?:\s*\.{3,}|\s*…|\s*\[…\]|\s*\[\.\.\.\]|\s*etc\.?|\s*-+|\s*_+)$', '', text)
        
        # Fix quotes
        text = text.replace(''', "'").replace(''', "'").replace('"', '"').replace('"', '"')
        
        # Ensure proper spacing around brand name
        brand_name = self.brand_name
        text = re.sub(rf'(\w){re.escape(brand_name)}', f'\\1 {brand_name}', text)
        text = re.sub(rf'{re.escape(brand_name)}(\w)', f'{brand_name} \\1', text)
        
        # Remove quotes around brand name
        text = text.replace(f'"{brand_name}"', brand_name)
        
        # Capitalize first character
        if text and text[0].islower():
            text = text[0].upper() + text[1:]
            
        return text.strip()
    
    def _create_fallback_tweet(self, fact_text, context_text, urls=None):
        """Create a fallback tweet if generation fails"""
        brand_name = self.brand_name
        
        # Identify if content mentions any of our topics
        topic = "sustainability"  # Default
        combined_text = (fact_text + " " + context_text).lower()
        
        for topic_name, keywords in self.sustainability_topics.items():
            for keyword in keywords:
                if keyword.lower() in combined_text:
                    topic = topic_name.replace("_", " ")
                    break
        
        # Better templates with guaranteed brand integration - more natural sounding
        templates = [
            f"Our latest data reveals companies reducing carbon emissions by 28% see growth in both profits and customer loyalty. {brand_name} is helping organizations track their real impact. #ClimateAction",
            
            f"{brand_name} research shows companies adopting renewable energy cut costs by 32% over 5 years. We're providing the data businesses need to make the clean energy transition. #SustainableBusiness",
            
            f"Water conservation techniques can reduce agricultural usage by 40% while increasing yields. {brand_name} analytics are helping farmers implement these sustainable practices effectively. #WaterConservation",
            
            f"We've found that 73% of consumers prefer brands with transparent sustainability practices. {brand_name} helps companies communicate their environmental impact clearly. #GreenBusiness"
        ]
        
        # Choose template based on identified topic
        chosen_template = templates[0]  # Default
        
        if "energy" in topic or "emission" in topic or "carbon" in topic:
            chosen_template = templates[1]
        elif "water" in topic or "agriculture" in topic or "farm" in topic:
            chosen_template = templates[2]
        elif "business" in topic or "consumer" in topic or "company" in topic:
            chosen_template = templates[3]
        
        # Process URLs if provided
        if urls:
            text, _ = self.url_processor.extract_urls(chosen_template)
            return self.url_processor.append_urls_to_text(text, urls, self.char_limit)
        
        return chosen_template

# Simple function for the API to use
def get_forced_branded_tweet(fact_content, context_content):
    """Generate a tweet that always includes the brand name"""
    generator = ForcedBrandedTweetGenerator()
    tweet = generator.generate_tweet(fact_content, context_content)
    
    # Double-check that URLs are included
    if fact_content and not any(url in tweet for url in ['http://', 'https://']):
        url_processor = URLProcessor()
        _, fact_urls = url_processor.extract_urls(fact_content)
        _, context_urls = url_processor.extract_urls(context_content)
        all_urls = fact_urls + context_urls
        
        if all_urls:
            # Extract any URLs that might already be in the tweet
            tweet_text, existing_urls = url_processor.extract_urls(tweet)
            # Add any URLs from the input content that aren't already in the tweet
            for url in all_urls:
                if url not in existing_urls:
                    existing_urls.append(url)
            # Reappend all URLs to ensure they're included
            tweet = url_processor.append_urls_to_text(tweet_text, existing_urls, 240)
    
    return tweet 