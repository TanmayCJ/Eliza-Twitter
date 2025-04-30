import os
import json
from groq import Groq
import logging

# Set up logging
logging.basicConfig(level=logging.ERROR)

# Load CHARACTER data
with open(r'D:\project\new\carbonsustain1\api\character_finalized1.json', 'r') as file:
    CHARACTER = json.load(file)

# Set up Groq client
client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

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
        # Convert the CHARACTER dictionary to a JSON string
        character_json = json.dumps(self.character, indent=2)

        full_prompt = (
            f"Use the following character data to generate a tweet:\n\n"
            f"{character_json}\n\n"
            "IMPORTANT GUIDELINES:\n"
            "1. Strictly stick to the content from the provided tweets\n"
            "2. Do not invent or hallucinate any facts, statistics, or entities\n"
            "3. Do not mention any handles/accounts that aren't in the source tweets\n"
            "4. Focus on climate facts and action\n"
            "5. Be concise and direct\n"
            "6. Do not add any URLs (they will be added automatically)\n"
            "7. Include at most 2 relevant hashtags\n\n"
            f"Use a {primary_tone} tone for about {primary_tone_weight * 100:.0f}% of the content.\n"
            f"Use a {secondary_tone} tone for about {secondary_tone_weight * 100:.0f}% of the content.\n\n"
            "8. Do not add include the message here is the regenerated tweet at the start of the tweet\n\n"
            "9. Make sure to use the content from the both the tweets and not just one of them\n\n"
            "10. Do not include any facts or statistics that are not present in the source tweets\n\n"
            f"{prompt}\n\nTweet:"
        )

        try:
            resp = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Use the character data to guide the response."},
                    {"role": "user", "content": full_prompt}
                ],
                model="llama3-8b-8192",
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=0.92,
                presence_penalty=0.1,
                frequency_penalty=0.5
            )
            generated = resp.choices[0].message.content
        except Exception as e:
            logging.error("Error generating tweet: %s", str(e))
            generated = "An error occurred while generating the tweet. Please try again."

        return generated
