import os
import json
import logging
from django.conf import settings
from google import genai  
from google.genai import types
from google.genai.types import (
    GenerateContentConfig,
    HarmCategory,
    HarmBlockThreshold,
    HttpOptions,
    SafetySetting,
) 
from dotenv import load_dotenv

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.ERROR)


with open(os.path.join(settings.BASE_DIR, 'combine_tweet', 'character3.json')) as file:
    CHARACTER = json.load(file)

# Configure the Gemini API key
client=genai.Client(api_key=os.getenv("YOUR_API_KEY"))

system_instruction = "You are twitter bot that combines data-driven factual reporting with sharp, edgy commentary to highlight climate issues and sustainability"
safety_settings = [
    SafetySetting(
        category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    ),
    SafetySetting(
        category=HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    ),
    SafetySetting(
        category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    ),
    SafetySetting(
        category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    ),
]
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

    def generate(self, prompt, max_tokens=60, temperature=0.7):
        messages = [
            {
                "role": "system",
                "content": (
                    f"You are {self.character['persona_name']}, a data-driven, friendly sustainability advocate.\n"
                    "• Always start with a clear fact, stat, or policy observation.\n"
                    "• Keep tweets to 1-2 sentences, 0-2 emojis (🌍 🚀 ✅), and 1-2 relevant hashtags.\n"
                    "• Use a rhetorical question or call-to-action in ~25% of tweets.\n"
                    f"• Only mention {self.character['persona_name']}—and then in a single, lightly boastful sentence—if proposing a solution, announcing an initiative, partnership, tool, or responding as the company.\n"
                    f"• That boast line should briefly state how {self.character['persona_name']} is helping, innovating, or supporting the cause.\n"
                    f"• Do NOT mention {self.character['persona_name']} in purely observational, critical, or third-party contexts."
                )
            },
            # Example tweets to demonstrate the style
            {
                "role": "assistant",
                "content": "Cutting 800 EPA grants jeopardizes critical climate infrastructure—what's our plan to rebuild resilience? 🌍 #ActOnClimate"
            },
            {
                "role": "assistant",
                "content": f"We've launched a real-time emissions dashboard for every organization to see its impact live. At {self.character['persona_name']}, we're empowering teams with transparent data to drive real change. 🚀 #CarbonData"
            },
            {
                "role": "assistant", 
                "content": f"Global CO₂ emissions hit 36.8 Gt in 2024—highest ever recorded. Ready to turn the tide? 🌍 #ClimateAction"
            },
            {
                "role": "assistant",
                "content": f"Our new alliance with leading researchers brings cutting-edge science into every carbon report. At {self.character['persona_name']}, we're uniting academia and industry to accelerate sustainability. 🔗 #ClimateCollab"
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        try:
            cfg = generation_config.copy()
            cfg["temperature"] = temperature
            cfg["max_output_tokens"] = max_tokens
            
            # Format the messages for Gemini's content structure
            formatted_prompt = "\n\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in messages])
            
            total_tokens = client.models.count_tokens(
                model="gemini-2.0-flash-001", 
                contents=formatted_prompt,
            )
            print("total_tokens: ", total_tokens)
            
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=formatted_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    top_p=0.95,
                    top_k=64,
                    max_output_tokens=60,
                    system_instruction=system_instruction,
                    safety_settings=safety_settings,
                    response_mime_type="text/plain"
                )
            )
            
            generated = response.text
            
        except Exception as e:
            logging.error("Error generating tweet: %s", e)
            generated = "An error occurred while generating the tweet. Please try again."
        
        print(generated)
        return generated
