import os
import json
import logging
from google import genai  # <-- add this
from dotenv import load_dotenv

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.ERROR)

# Load CHARACTER data
with open(r'D:\project\new\carbonsustain1\api\character3.json', 'r', encoding='utf-8') as file:
    CHARACTER = json.load(file)

# Configure the Gemini API key
client=genai.Client(api_key=os.getenv("YOUR_API_KEY"))# <-- use your env var here

# Keep your existing generation_config if you like:
generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 60,
    "response_mime_type": "text/plain",
}

class TweetLLM:
    def __init__(self):
        self.character = CHARACTER
        self.examples = self.character['example_tweets']

        self.persona_base = (
            f"Persona: {self.character['persona_name']} — {self.character['persona_description']}\n"
            f"Tone: {', '.join(self.character['tone']['primary'])}\n"
            f"Style guidelines: {self.character['style_guidelines']}\n"
            f"EXAMPLE TWEETS:\n"
        )

        '''for ex in self.examples['fact']:
            self.persona_base += f"- {ex}\n"
        for ex in self.examples['mixed']:
            self.persona_base += f"- {ex}\n"'''

    def generate(self, prompt, max_tokens=60, temperature=0.7):
        character_json = json.dumps(self.character, indent=2)
        primary_tone = ', '.join(self.character['tone']['primary'])
        secondary_tone = ', '.join(self.character['tone']['secondary'])
        primary_tone_weight = 0.7
        secondary_tone_weight = 0.3

        full_prompt = (
            "IMPORTANT GUIDELINES:\n"
            "1. Strictly stick to the content from the provided tweets\n"
            "2. Do not invent or hallucinate any facts, statistics, or entities\n"
            "3. Do not mention any handles/accounts that aren't in the source tweets\n"
            "4. Focus on climate facts and action\n"
            "5. Be concise and direct\n"
            "6. Do not add any URLs (they will be added automatically)\n"
            "7. Include at most 2 relevant hashtags\n\n"
            "8. Do not include the message 'here is the regenerated tweet' at the start\n"
            "9. Use content from both tweets, not just one\n"
            "10. Do not include any facts or statistics not present in the source tweets.\n"
            f"Use the following character data to generate a tweet:\n"
            f"{character_json}\n"
            f"Use a {primary_tone} tone for about {int(primary_tone_weight*100)}% of the content.\n"
            f"Use a {secondary_tone} tone for about {int(secondary_tone_weight*100)}% of the content.\n"
            f"{prompt}\nTweet:"
        )

        try:
            cfg = generation_config.copy()
            cfg["temperature"] = temperature
            cfg["max_output_tokens"] = max_tokens
            total_tokens = client.models.count_tokens(
                model="gemini-2.0-flash", contents=full_prompt
            )
            print("total_tokens: ", total_tokens)
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=full_prompt
                
            )
            generated = response.text
        except Exception as e:
            logging.error("Error generating tweet: %s", e)
            generated = "An error occurred while generating the tweet. Please try again."
        print(generated)

        return generated

    def check_tweet_relatedness(self, tweet1, tweet2, threshold=0.7):
        """
        Checks if two tweets are topically related.
        
        Args:
            tweet1 (str): The first tweet content
            tweet2 (str): The second tweet content
            threshold (float): Confidence threshold to consider tweets related (0.0-1.0)
            
        Returns:
            bool: True if tweets are related, False otherwise
        """
        
        # Construct a focused prompt for relation categorization
        relatedness_prompt = (
            "Your task is to determine if two climate/sustainability tweets are topically related.\n\n"
            "TWEET 1:\n"
            f"{tweet1}\n\n"
            "TWEET 2:\n"
            f"{tweet2}\n\n"
            "INSTRUCTIONS:\n"
            "1. Analyze the central topic, entities, and claims in each tweet\n"
            "2. Determine if they discuss the same environmental issue, policy, or solution\n"
            "3. Calculate the relatedness score between the two tweets\n"
            "4. If the relatedness score is less than 0.7, return False\n"
            "5. Respond with ONLY ONE of these exact phrases:\n"
            "   - 'RELATED' - if they share core topics and could be merged coherently\n"
            "   - 'UNRELATED' - if combining them would result in an unfocused, disconnected message\n\n"
            "Response:"
        )
        
        try:
            # Using a low temperature for more deterministic results
            cfg = generation_config.copy()
            cfg["temperature"] = 0.1
            cfg["max_output_tokens"] = 10
            # Call the Gemini API
            total_tokens = client.models.count_tokens(
                model="gemini-2.0-flash", contents=relatedness_prompt
            )
            print("total_tokens: ", total_tokens)
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=relatedness_prompt
            )
            
            result = response.text.strip().upper()
            print(result)
            # Extract just the decision
            if "UNRELATED" in result:
                return False
            elif "RELATED" in result:
                return True
            else:
                # If the model didn't respond with the expected format, 
                # default to considering them unrelated
                logging.warning(f"Unexpected relatedness response: {result}")
                return False
                
        except Exception as e:
            logging.error(f"Error checking tweet relatedness: {str(e)}")
            # On error, default to True to attempt merging
            return True
