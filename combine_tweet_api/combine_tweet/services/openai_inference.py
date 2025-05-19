import os
import json
import logging
# from django.conf import settings # Removed as not used
# Removed google.genai imports
# from google import genai
# from google.genai import types
# from google.genai.types import (...)
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.ERROR)

# Configure and instantiate the OpenAI client
client = OpenAI()

# Updated system instruction based on the persona
system_instruction = "You are CarbonSustainAI, the voice of CarbonSustain — a climate-smart, data-driven guide helping small and mid-sized businesses (SMBs) track, reduce, and offset their carbon emissions using AI-powered insights and on-chain transparency."

# Removed safety_settings
# safety_settings = [...]


class TweetLLM:
    # The __init__ method is no longer needed
    # def __init__(self):
    #     pass

    def generate(self, factual_tweet: str, rant_tweet: str, max_tokens: int = 100, temperature: float = 0.7):
        # Use a2.py to find relevant tweets based on the factual tweet
        # These tweets will serve as the "reference" context
        a2_tweets_context = ""
        try:
            # *** MODIFIED IMPORT STATEMENT ***
            # Assuming a2.py is in the same directory (services/) and it's part of the package
            import a2
            relevant_tweets_from_a2 = a2.top3_matches(factual_tweet)
            a2_tweets_text = [tweet for tweet, score in relevant_tweets_from_a2]
            if a2_tweets_text:
                 # Label these tweets clearly as the reference/additional context
                 a2_tweets_context = "\n--- Relevant tweets from knowledge base (serving as reference context) ---\n" + "\n---\n".join(a2_tweets_text) + "\n--------------------------------------------------------------------\n\n"
        except ImportError:
            # If direct import fails, try relative import from current directory
            try:
                from . import a2
                relevant_tweets_from_a2 = a2.top3_matches(factual_tweet)
                a2_tweets_text = [tweet for tweet, score in relevant_tweets_from_a2]
                if a2_tweets_text:
                    a2_tweets_context = "\n--- Relevant tweets from knowledge base (serving as reference context) ---\n" + "\n---\n".join(a2_tweets_text) + "\n--------------------------------------------------------------------\n\n"
                print(a2_tweets_context)
            except ImportError:
                 logging.error("Could not import a2.py. Ensure it is in the same directory as openai_inference.py and the application is run as a package.")
                 a2_tweets_context = "" # No additional context if import fails
            except Exception as e:
                logging.error("Error finding relevant tweets with a2.py after trying relative import: %s", e)
                a2_tweets_context = "" # No additional context if matching fails
        except Exception as e:
            logging.error("Error finding relevant tweets with a2.py after trying direct import: %s", e)
            a2_tweets_context = "" # No additional context if matching fails
        

        # Construct the full prompt string for the user message
        full_prompt_text = (
            "You will be provided with a factual tweet, a rant tweet, and several relevant tweets from a knowledge base (serving as reference context).\n\n"
            "🎯 Your task:\n\n"
            "Fuse the truth from the factual tweet with the emotion or urgency of the rant tweet.\n\n"
            "Use the relevant tweets from the knowledge base to anchor your tone and viewpoint — calm, clear, constructive, reflecting CarbonSustain's voice.\n\n"
            "Write a single, original tweet in CarbonSustain's voice that:\n\n"
            "Acknowledges frustration or irony.\n\n"
            "Reframes the issue with insight and optimism.\n\n"
            "Offers a solution, mindset shift, or practical action.\n\n"
            "Optionally mentions CarbonSustain's philosophy (e.g. measurement, AI, supply chain visibility) without sounding like a pitch.\n\n"
            "Ends with a strong closer – a mic drop, hopeful insight, or hashtag.\n\n"
            "🧠 Tone & Style:\n\n"
            "Calm, clear, slightly witty.\n\n"
            "Feels like a climate-smart advisor, not a corporate brochure.\n\n"
            "Never panicked. Never preachy. Never doomscroll bait.\n\n"
            "Uses short, punchy lines. Avoids filler. Rhetorical questions welcome.\n\n"
            "📝 Writing Rules:\n\n"
            "1–3 lines max. No threads.\n\n"
            "Be informative and emotionally aware.\n\n"
            "Mix activist sharpness with solution-focused clarity.\n\n"
            "✅ Example:\n\n"
            "Factual Tweet: \"Scope 3 emissions make up 70%+ of corporate carbon footprints. Yet most companies don't even measure them.\"\n\n"
            "Rant Tweet: \"Let me guess. Scope 3 means I'm responsible for my supplier's supplier's diesel truck. Awesome.\"\n\n"
            "Reference Tweets (from knowledge base): \"Scope 3 isn't a blame game. It's a map of where your carbon hides—and where your impact can shine. We help SMBs measure the invisible.\"\n\n"
            "✨ Example Output Tweet:\n"
            "\"Scope 3 sounds like a nightmare. But it's really a flashlight. You can't shrink what you can't see. Start with what you can track—your vendors, commutes, cloud usage. Visibility is power. #CarbonAccounting\"\n\n"
            "--- Now generate a tweet based on the following inputs ---\n\n"
            f"Factual Tweet: \"{factual_tweet}\"\n\n"
            f"Rant Tweet: \"{rant_tweet}\"\n\n"
            f"{a2_tweets_context}" # Include the relevant tweets from a2.py as reference context
            "✨ Output Tweet:"
        )

        try:
            # Use OpenAI Chat Completions API with the client instance
            response = client.chat.completions.create(
                model="gpt-4o-mini", # Using a cost-effective and capable model, you can change this
                messages=[
                    {"role": "system", "content": system_instruction}, # System instruction as a system message
                    {"role": "user", "content": full_prompt_text} # The detailed prompt as a user message
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            # Extract the generated text from the OpenAI response
            generated = response.choices[0].message.content

        except Exception as e:
            logging.error("Error generating tweet with OpenAI: %s", e)
            generated = "An error occurred while generating the tweet. Please try again."

        print(generated)
        return generated
