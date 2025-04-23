import os
import re
import openai
from openai import OpenAI
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
persona = """
You are CarbonSustain, a data-driven climate voice on Twitter.
Your tweets are fact-first, call out greenwashing, and drive climate accountability.
Use stats, avoid fluff. Always aim to educate or provoke real action.
"""

class TweetLLM:
    def __init__(self, model_path=None, device=None):
        # Keep the original initialization parameters for compatibility
        # But we'll use OpenAI API instead
        self.model_path = model_path
        self.device = device
        
        # Check if API key is set
        if not client.api_key or client.api_key == "YOUR_OPENAI_API_KEY_HERE":
            if os.environ.get("OPENAI_API_KEY"):
                client.api_key = os.environ.get("OPENAI_API_KEY")
            else:
                raise ValueError("OpenAI API key not set. Please set it in the code or as OPENAI_API_KEY environment variable.")

    def generate(self, prompt, max_tokens=60, temperature=0.7):
        full_prompt = f"""
{persona.strip()}

IMPORTANT GUIDELINES:
1. Strictly stick to the content from the provided tweets
2. Do not invent or hallucinate any facts, statistics, or entities
3. Do not mention any handles/accounts that aren't in the source tweets
4. Focus on climate facts and action
5. Be concise and direct

Combine these two tweets into a single coherent message that maintains factual accuracy:

{prompt}

Tweet:
"""
        
        # Use OpenAI API instead of local model
        try:
            response = client.chat.completions.create(
                model="gpt-4",  # Use GPT-4 for best quality, or "gpt-3.5-turbo" for faster/cheaper
                messages=[
                    {"role": "system", "content": persona.strip()},
                    {"role": "user", "content": full_prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=0.92,
                presence_penalty=0.1,
                frequency_penalty=0.5
            )
            
            # Extract the generated text
            generated_text = response.choices[0].message.content
            
        except Exception as e:
            print(f"Error calling OpenAI API: {str(e)}")
            # Fallback message in case of API error
            generated_text = "Climate action requires factual, data-driven approaches. #ClimateAction"
        
        # Post-process the tweet to clean up common issues
        tweet = self._post_process_tweet(generated_text)
        return tweet
    
    def _post_process_tweet(self, tweet):
        """Clean up the generated tweet to fix common issues"""
        # Remove any instances of "Tweet:" that might have been generated
        tweet = re.sub(r'^Tweet:\s*', '', tweet)
        
        # Fix common hashtag formatting issues (#This should be #This)
        tweet = re.sub(r'#(\w+\s+\w+)', r'#\1', tweet)
        
        # Remove any URL fragments that might have been generated
        # We'll add the real URLs later in the API
        url_pattern = re.compile(r'https?://\S+')
        tweet = url_pattern.sub('', tweet).strip()
        
        # Remove multiple spaces
        tweet = re.sub(r'\s+', ' ', tweet).strip()
        
        # Remove excessive hashtags (keep at most 3)
        hashtags = re.findall(r'#\w+', tweet)
        if len(hashtags) > 3:
            for tag in hashtags[3:]:
                tweet = tweet.replace(tag, '')
        
        # Make sure the tweet is concise
        if len(tweet) > 240:
            tweet = tweet[:237] + "..."
            
        return tweet.strip()