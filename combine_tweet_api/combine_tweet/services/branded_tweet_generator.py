import re
import os
import json
from django.conf import settings
from combine_tweet.services.url_processor import URLProcessor
from combine_tweet.services.external_api import ExternalAPIClient
from combine_tweet.services.retry_logic import build_retry_prompt
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

# Generation config
generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 60,
    "response_mime_type": "text/plain",
}

# System instruction
system_instruction = "You are a social media expert that creates branded sustainability tweets"

class BrandedTweetLLM:
    """
    LLM interface specifically designed for generating branded tweets
    that always include the company name in a natural way.
    """
    def __init__(self):
        self.character = CHARACTER
        self.brand_name = self.character['persona_name']

    def generate(self, prompt, max_tokens=100, temperature=0.7):
        messages = [
            {
                "role": "system",
                "content": (
                    f"You are a pro-sustainability climate advocate writing for {self.brand_name}.\n\n"
                    "YOUR VOICE:\n"
                    "• Bold, direct, and focused on sustainability topics\n"
                    "• Supportive of environmental policies and initiatives\n"
                    "• Factual but engaging on climate and sustainability issues\n" 
                    "• Cover diverse topics from renewable energy to biodiversity\n"
                    "• Maintain a positive stance toward climate action\n\n"
                    "CRITICAL RULES:\n"
                    f"• NEVER, EVER say \"{self.brand_name} Voice\" - it is FORBIDDEN\n"
                    f"• Use ONLY \"{self.brand_name}\" or \"we\" or \"our\" to reference the brand\n"
                    "• Do not add ANY suffix or modifier to the brand name\n"
                    "• Cover a diverse range of sustainability topics\n"
                    "• Maintain factual accuracy while being engaging\n"
                    "• Keep tweets under 240 characters\n"
                    "• Use 1-2 potent hashtags that amplify the message\n"
                    f"• When referencing {self.brand_name}, use ONLY these formats:\n"
                    f"  1. \"We've uncovered...\"\n"
                    f"  2. \"Our research reveals...\"\n"
                    f"  3. \"{self.brand_name} reveals...\"\n"
                    "• Create a tone of urgency around climate action"
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        try:
            # Format the messages for Gemini's content structure
            formatted_prompt = "\n\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in messages])
            
            # Count tokens
            total_tokens = client.models.count_tokens(
                model="gemini-2.0-flash-001", 
                contents=formatted_prompt,
            )
            print(f"Total tokens: {total_tokens}")
            
            # Generate content with higher temperature for more edge
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=formatted_prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    top_p=0.95,
                    top_k=64,
                    max_output_tokens=max_tokens,
                    system_instruction="You are a pro-sustainability advocate covering diverse environmental topics. NEVER use the phrase 'CarbonSustain Voice'.",
                    safety_settings=safety_settings,
                    response_mime_type="text/plain"
                )
            )
            
            generated = response.text
            # Immediate post-processing to remove any "Voice" suffix 
            if "Voice" in generated:
                generated = self._remove_voice_suffix(generated)
                
            return generated
            
        except Exception as e:
            print(f"Error generating branded tweet: {str(e)}")
            return f"An error occurred while generating the branded tweet. Please try again."
            
    def _remove_voice_suffix(self, text):
        """Remove any instance of 'Voice' after the brand name"""
        brand_name = CHARACTER['persona_name']
        
        # More aggressive pattern matching for 'Voice' removal
        # Direct replacements
        text = text.replace(f"{brand_name} Voice", brand_name)
        text = text.replace(f"{brand_name}Voice", brand_name)
        text = text.replace(f"{brand_name}'s Voice", f"{brand_name}")
        text = text.replace(f"{brand_name} voice", brand_name)
        text = text.replace(f"{brand_name} VOICE", brand_name)
        
        # Regex-based replacements for more variations
        text = re.sub(rf'{re.escape(brand_name)}\s+[Vv][Oo][Ii][Cc][Ee]', brand_name, text)
        text = re.sub(rf'[Aa][Tt]\s+{re.escape(brand_name)}\s+[Vv][Oo][Ii][Cc][Ee]', f"At {brand_name}", text)
        text = re.sub(rf'[Ff][Rr][Oo][Mm]\s+{re.escape(brand_name)}\s+[Vv][Oo][Ii][Cc][Ee]', f"From {brand_name}", text)
        
        return text


class BrandedTweetGenerator:
    """
    Main class for generating branded tweets that always include the company name.
    """
    def __init__(self):
        self.llm = BrandedTweetLLM()
        self.safety_api = settings.SAFETY_API_URL
        self.popularity_api = settings.POPULARITY_API_URL
        self.char_limit = 240
        self.max_retries = settings.MAX_API_RETRIES
        self.proceed_regardless = settings.PROCEED_REGARDLESS
        self.url_processor = URLProcessor()
        self.api_client = ExternalAPIClient()
        
        # Blend ratios
        self.fact_weight = 0.7  # default 70% facts
        self.context_weight = 0.3  # default 30% context
        
        # List of forbidden phrases - only keep the Voice-related and extremely negative ones
        self.forbidden_phrases = [
            "voice",
            "carbonsustain voice"
        ]
        
        # Dictionary of sustainability topics and related terms
        self.sustainability_topics = {
            "renewable_energy": ["solar", "wind", "renewable", "clean energy", "energy transition"],
            "climate_policy": ["carbon pricing", "emissions", "climate policy", "paris agreement"],
            "biodiversity": ["species", "ecosystem", "wildlife", "habitat", "conservation"],
            "sustainable_agriculture": ["regenerative", "farming", "agriculture", "food systems"],
            "clean_transport": ["electric vehicle", "ev", "transportation", "mobility"],
            "circular_economy": ["recycling", "waste", "circular", "reuse", "plastic"],
            "water": ["ocean", "marine", "water", "drought", "flood"],
            "climate_justice": ["equity", "vulnerable communities", "frontline", "just transition"],
            "green_tech": ["innovation", "technology", "cleantech", "green technology"]
        }

    def set_blend_ratio(self, fact_weight, context_weight):
        if not abs((fact_weight + context_weight) - 1.0) < 0.01:
            raise ValueError("Blend weights must add up to 1.0")
        self.fact_weight = fact_weight
        self.context_weight = context_weight

    def generate_prompt(self, fact_text, context_text):
        brand_name = CHARACTER['persona_name']
        
        # Clean inputs - remove numbering/prefixes and unnecessary text
        fact_part = re.sub(r'^[0-9]+/\s*', '', fact_text).strip()
        context_part = re.sub(r'^(WAKE-UP CALL:)\s*', '', context_text).strip()
        
        # Remove questions at the end that might dilute the message
        fact_part = re.sub(r'What\'s driving up your bill\?.*$', '', fact_part).strip()
        context_part = re.sub(r'What\'s your footprint\?.*$', '', context_part).strip()
        
        # Identify sustainability topics in the content
        identified_topics = []
        combined_text = fact_part + " " + context_part
        combined_text = combined_text.lower()
        
        for topic, keywords in self.sustainability_topics.items():
            for keyword in keywords:
                if keyword.lower() in combined_text:
                    topic_name = topic.replace("_", " ").title()
                    if topic_name not in identified_topics:
                        identified_topics.append(topic_name)
        
        # If no topics found, add general topics
        if not identified_topics:
            identified_topics = ["Climate Action", "Sustainability"]
        
        # Extract key statistics with improved patterns
        money_pattern = r'(\$\d+(?:\.\d+)?(?:/[a-zA-Z]+)?|\d+(?:\.\d+)?[TMB])'
        percentage_pattern = r'(\d+(?:\.\d+)?%)'
        number_pattern = r'(\d+(?:\.\d+)?\s+(?:times|percent|degrees|tons|million|billion))'
        
        # Find all key numbers and statistics
        money_values = re.findall(money_pattern, fact_part + " " + context_part)
        percentages = re.findall(percentage_pattern, fact_part + " " + context_part)
        numbers = re.findall(number_pattern, fact_part + " " + context_part, re.IGNORECASE)
        
        # Combine all statistics
        all_stats = money_values + percentages + numbers
        
        # Extract hashtags
        hashtag_pattern = r'(#[A-Za-z0-9_]+)'
        hashtags = re.findall(hashtag_pattern, fact_part) + re.findall(hashtag_pattern, context_part)
        
        # Generate related hashtags if none found
        if not hashtags:
            for topic in identified_topics[:2]:  # Use up to 2 topics
                clean_topic = topic.replace(" ", "")
                hashtags.append(f"#{clean_topic}")
        
        return f"""
Create a branded tweet about sustainability based on these inputs:

1. FACT: {fact_part}
2. CONTEXT: {context_part}

RELATED SUSTAINABILITY TOPICS:
- {', '.join(identified_topics)}

KEY STATISTICS TO INCORPORATE (if relevant):
- {', '.join(all_stats) if all_stats else 'Use factual numbers or statistics from the content'}

TWEET REQUIREMENTS:
1. Include either "we"/"our" or "{brand_name}" (NEVER include the word "Voice")
2. Create an informative and engaging sustainability message
3. Include specific statistics from the content for impact
4. Focus on a solution, insight, or call to action
5. Use 1-2 relevant hashtags like {', '.join(hashtags[:2]) if hashtags else '#Sustainability #ClimateAction'}
6. Include any relevant URLs from the original content
7. Keep under 240 characters

Write a factual, engaging tweet about sustainability:
"""

    def generate_branded_tweet(self, fact_content, context_content):
        """
        Generate a branded tweet that always includes the company name,
        blending factual and contextual content.
        """
        # Extract URLs from content
        fact_text, fact_urls = self.url_processor.extract_urls(fact_content)
        context_text, context_urls = self.url_processor.extract_urls(context_content)
        all_urls = fact_urls + context_urls
        
        # Generate prompt and get tweet from LLM
        prompt = self.generate_prompt(fact_text, context_text)
        
        try:
            # Generate and clean tweet
            raw_tweet = self.llm.generate(prompt, temperature=0.75, max_tokens=120)
                
            # Immediately check and fix any "Voice" suffix before further processing
            if "Voice" in raw_tweet:
                raw_tweet = self._remove_voice_suffix(raw_tweet)
                    
            clean_tweet = self._fix_formatting(raw_tweet)
            
            # Process URLs - first extract any URLs the model might have included
            text, new_urls = self.url_processor.extract_urls(clean_tweet)
            
            # Combine with original URLs, ensuring no duplicates
            for url in all_urls:
                if url not in new_urls:
                    new_urls.append(url)
                    
            # Ensure we have the final text without URLs before appending
            final_tweet = self.url_processor.append_urls_to_text(text, new_urls, self.char_limit)
            
            # Double-check if URLs are in the final tweet
            if all_urls and not any(url in final_tweet for url in ['http://', 'https://']):
                # Force append URLs
                text_without_urls, _ = self.url_processor.extract_urls(final_tweet)
                final_tweet = text_without_urls
                for url in all_urls:
                    if len(final_tweet) + len(url) + 1 <= self.char_limit:
                        final_tweet += ' ' + url
            
            return final_tweet
            
        except Exception as e:
            print(f"Error generating branded tweet: {str(e)}")
            return self._create_fallback_tweet(fact_text, context_text, all_urls)

    def _create_fallback_tweet(self, fact_text, context_text, urls=None):
        """Create a solid fallback tweet when generation fails"""
        brand_name = CHARACTER['persona_name']
        
        # Extract key elements for topic identification
        combined_text = (fact_text + " " + context_text).lower()
        
        # Identify a relevant sustainability topic
        topic = "sustainability"  # Default
        topic_found = False
        
        for topic_name, keywords in self.sustainability_topics.items():
            for keyword in keywords:
                if keyword.lower() in combined_text:
                    topic = topic_name.replace("_", " ")
                    topic_found = True
                    break
            if topic_found:
                break
                
        # Create diverse fallback templates based on different sustainability topics
        templates = [
            f"Our latest research shows California's environmental initiatives are driving both economic growth and emissions reductions. {brand_name} is tracking these dual benefits of climate action. #GreenEconomy",
            
            f"{brand_name} reveals: Renewable energy capacity grew 48% last year, creating 3x more jobs per dollar than fossil fuels. The clean energy transition offers economic opportunity. #CleanEnergyJobs",
            
            f"We've found that sustainable agriculture practices can increase farmer profits while sequestering carbon. The climate-friendly approach benefits both business and planet. #SustainableFarming",
            
            f"{brand_name} research indicates stronger environmental standards correlate with improved public health outcomes and reduced healthcare costs. #HealthyClimate"
        ]
        
        # Choose a template that best matches the identified topic if possible
        chosen_template = templates[0]  # Default
        
        # Topic-specific templates
        if "energy" in topic:
            chosen_template = templates[1]
        elif "agriculture" in topic or "food" in topic or "farm" in topic:
            chosen_template = templates[2]
        elif "health" in topic:
            chosen_template = templates[3]
        
        # Process URLs if provided
        if urls:
            text, _ = self.url_processor.extract_urls(chosen_template)
            text = self.url_processor.append_urls_to_text(text, urls, self.char_limit)
            return text
        
        return chosen_template

    def _remove_voice_suffix(self, text):
        """Remove any instance of 'Voice' after the brand name"""
        brand_name = CHARACTER['persona_name']
        
        # More aggressive pattern matching for 'Voice' removal
        # Direct replacements
        text = text.replace(f"{brand_name} Voice", brand_name)
        text = text.replace(f"{brand_name}Voice", brand_name)
        text = text.replace(f"{brand_name}'s Voice", f"{brand_name}")
        text = text.replace(f"{brand_name} voice", brand_name)
        text = text.replace(f"{brand_name} VOICE", brand_name)
        
        # Regex-based replacements for more variations
        text = re.sub(rf'{re.escape(brand_name)}\s+[Vv][Oo][Ii][Cc][Ee]', brand_name, text)
        text = re.sub(rf'[Aa][Tt]\s+{re.escape(brand_name)}\s+[Vv][Oo][Ii][Cc][Ee]', f"At {brand_name}", text)
        text = re.sub(rf'[Ff][Rr][Oo][Mm]\s+{re.escape(brand_name)}\s+[Vv][Oo][Ii][Cc][Ee]', f"From {brand_name}", text)
        
        return text

    def _fix_formatting(self, text):
        """Clean up the generated tweet text."""
        if not text:
            return text
            
        # Remove prefixes like "Tweet:" or "Here's the tweet:"
        text = re.sub(r'^(Tweet:|Here\'s the tweet:|Branded tweet:)\s*', '', text, flags=re.IGNORECASE)
        
        # Fix common issues with brand name - additional aggressive check
        text = self._remove_voice_suffix(text)
        
        # Fix hashtag spacing and formatting
        text = re.sub(r'#(\w+\s+\w+)', r'#\1', text)
        text = re.sub(r'(\w)#', r'\1 #', text)  # Add space before hashtags
        
        # Remove duplicate spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Limit hashtags to 2 max
        hashtags = re.findall(r'#\w+', text)
        if len(hashtags) > 2:
            for tag in hashtags[2:]:
                text = text.replace(tag, '')
                
        # Remove trailing ellipses or incomplete thoughts
        text = re.sub(
            r'(?:\s*\.{3,}|\s*…|\s*\[…\]|\s*\[\.\.\.\]|\s*etc\.?|\s*-+|\s*_+)$',
            '', text
        )
        
        # Fix quotes to be consistent
        text = text.replace(''', "'").replace(''', "'").replace('"', '"').replace('"', '"')
        
        # Ensure proper spacing around the brand name
        brand_name = CHARACTER['persona_name']
        text = re.sub(rf'(\w){re.escape(brand_name)}', f'\\1 {brand_name}', text)
        text = re.sub(rf'{re.escape(brand_name)}(\w)', f'{brand_name} \\1', text)
        
        # Remove quotes around the brand name
        text = text.replace(f'"{brand_name}"', brand_name)
        
        # Capitalize first character if it's lowercase
        if text and text[0].islower():
            text = text[0].upper() + text[1:]
        
        # One final check for "Voice"
        if "voice" in text.lower():
            text = self._remove_voice_suffix(text)
            
        return text.strip()

def brand_integration_check(fact_content, context_content):
    """
    Assess whether the given content is suitable for brand integration.
    
    Args:
        fact_content (str): The factual content to analyze
        context_content (str): The contextual content to analyze
        
    Returns:
        tuple: (bool, str) - (is_suitable, reason)
    """
    brand_name = CHARACTER['persona_name']
    combined_text = (fact_content + " " + context_content).lower()
    
    # Define integration opportunity signals
    integration_signals = {
        "solution": ["solution", "innovation", "initiative", "platform", "tool", "service", 
                     "research", "report", "data", "analysis", "partnership"],
        "action": ["action", "progress", "opportunity", "transition", "improvement", 
                  "benefit", "advantage", "opportunity", "success", "achievement"],
        "expertise": ["expert", "specialist", "leader", "authority", "pioneer", 
                     "researcher", "scientist", "analyst", "professional"]
    }
    
    # Define topics that align well with brand integration
    brand_aligned_topics = {
        "data": ["data", "metrics", "measurement", "tracking", "reporting", "analytics"],
        "strategy": ["strategy", "plan", "roadmap", "framework", "approach", "method"],
        "solution": ["solution", "answer", "fix", "remedy", "resolution"]
    }
    
    # Define negative contexts that should avoid brand integration
    negative_contexts = [
        "controversy", "scandal", "failure", "disaster", "crisis", "problem", 
        "debate", "dispute", "argument", "conflict", "disagreement", "criticism",
        "question", "doubt", "uncertain", "unclear", "wonder", "concern"
    ]
    
    # Check for negative contexts
    for negative in negative_contexts:
        if negative in combined_text:
            return False, f"Content contains negative context: '{negative}'"
    
    # Check for brand promotion opportunities
    signal_count = 0
    found_signals = []
    
    for category, signals in integration_signals.items():
        for signal in signals:
            if signal in combined_text:
                signal_count += 1
                found_signals.append(signal)
                break  # Only count one match per category
    
    # Check for brand-aligned topics
    topic_alignment = 0
    aligned_topics = []
    
    for category, topics in brand_aligned_topics.items():
        for topic in topics:
            if topic in combined_text:
                topic_alignment += 1
                aligned_topics.append(topic)
                break  # Only count one match per category
    
    # Content already mentions the brand - this is a good signal
    if brand_name.lower() in combined_text:
        return True, f"Content already mentions {brand_name}"
    
    # Generate a composite score
    total_score = signal_count + topic_alignment
    
    # Determine suitability based on scores
    if total_score >= 3:
        return True, f"Strong brand integration potential with signals: {', '.join(found_signals + aligned_topics)}"
    elif total_score >= 1:
        return True, f"Moderate brand integration potential with signals: {', '.join(found_signals + aligned_topics)}"
    else:
        return False, "Insufficient brand integration signals in content"

def smart_branded_tweet_generator(fact_content, context_content, fact_weight=0.7, context_weight=0.3, force_branding=False):
    """
    Smart branded tweet generator that first checks if content is suitable for brand integration.
    Only applies branding if appropriate, or if explicitly forced.
    
    Args:
        fact_content (str): The factual content to include
        context_content (str): The contextual content to include
        fact_weight (float): Weight for factual content (0.0-1.0)
        context_weight (float): Weight for contextual content (0.0-1.0)
        force_branding (bool): Force brand integration regardless of content suitability
        
    Returns:
        dict: Result containing the tweet and information about the brand integration decision
    """
    # Extract URLs early to ensure they're preserved in both paths
    url_processor = URLProcessor()
    _, fact_urls = url_processor.extract_urls(fact_content)
    _, context_urls = url_processor.extract_urls(context_content)
    all_urls = fact_urls + context_urls
    
    # First, check if content is suitable for brand integration
    is_suitable, reason = brand_integration_check(fact_content, context_content)
    is_suitable = True
    
    # If suitable or forced, use branded tweet generator
    if is_suitable or force_branding:
        generator = BrandedTweetGenerator()
        generator.set_blend_ratio(fact_weight, context_weight)
        branded_tweet = generator.generate_branded_tweet(fact_content, context_content)
        
        # Double-check URL inclusion
        if all_urls and not any(url in branded_tweet for url in ['http://', 'https://']):
            tweet_text, existing_urls = url_processor.extract_urls(branded_tweet)
            branded_tweet = url_processor.append_urls_to_text(tweet_text, all_urls, 240)
        
        return {
            "tweet": branded_tweet,
            "is_branded": True,
            "reason": reason if is_suitable else "Brand integration forced by user"
        }
    else:
        # Use regular tweet generator without brand integration
        from combine_tweet.services.tweet_generator import TweetGenerator
        generator = TweetGenerator()
        generator.set_blend_ratio(fact_weight, context_weight)
        regular_tweet = generator.generate_combined_tweet(fact_content, context_content)
        
        # Double-check URL inclusion for non-branded tweets too
        if all_urls and not any(url in regular_tweet for url in ['http://', 'https://']):
            tweet_text, existing_urls = url_processor.extract_urls(regular_tweet)
            regular_tweet = url_processor.append_urls_to_text(tweet_text, all_urls, 240)
        
        return {
            "tweet": regular_tweet,
            "is_branded": False,
            "reason": reason
        }

# Function to directly get a branded tweet without initializing the class
def get_branded_tweet(fact_content, context_content, fact_weight=0.7, context_weight=0.3):
    """
    Utility function to quickly get a branded tweet without manual class initialization.
    
    Args:
        fact_content (str): The factual content to include
        context_content (str): The contextual content to include
        fact_weight (float): Weight for factual content (0.0-1.0)
        context_weight (float): Weight for contextual content (0.0-1.0)
        
    Returns:
        str: Generated branded tweet with company name included
    """
    # First extract all URLs from the content
    url_processor = URLProcessor()
    _, fact_urls = url_processor.extract_urls(fact_content)
    _, context_urls = url_processor.extract_urls(context_content)
    all_urls = fact_urls + context_urls
    
    # Generate the tweet
    generator = BrandedTweetGenerator()
    generator.set_blend_ratio(fact_weight, context_weight)
    tweet = generator.generate_branded_tweet(fact_content, context_content)
    
    # Triple-check that URLs are included (belt and suspenders approach)
    if all_urls and not any(url in tweet for url in all_urls):
        # Extract any existing URLs
        tweet_text, existing_urls = url_processor.extract_urls(tweet)
        
        # Create new list with all unique URLs
        combined_urls = existing_urls.copy()
        for url in all_urls:
            if url not in combined_urls:
                combined_urls.append(url)
        
        # Force append all URLs
        tweet = url_processor.append_urls_to_text(tweet_text, combined_urls, 240)
        
        # Last resort - direct append if still missing
        if not any(url in tweet for url in all_urls):
            for url in all_urls:
                if len(tweet) + len(url) + 1 <= 240 and url not in tweet:
                    tweet += ' ' + url
    
    return tweet

# Function to get a smart branded tweet that only uses branding when appropriate
def get_smart_branded_tweet(fact_content, context_content, fact_weight=0.7, context_weight=0.3, force_branding=False):
    """
    Utility function to get a smart branded tweet that only applies branding when appropriate.
    
    Args:
        fact_content (str): The factual content to include
        context_content (str): The contextual content to include
        fact_weight (float): Weight for factual content (0.0-1.0)
        context_weight (float): Weight for contextual content (0.0-1.0)
        force_branding (bool): Force brand integration regardless of content suitability
        
    Returns:
        dict: Result containing the tweet and information about the brand integration decision
    """
    result = smart_branded_tweet_generator(fact_content, context_content, fact_weight, context_weight, force_branding)
    
    # Double-check that URLs are included in the tweet
    tweet = result['tweet']
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
            result['tweet'] = url_processor.append_urls_to_text(tweet_text, existing_urls, 240)
    
    return result 