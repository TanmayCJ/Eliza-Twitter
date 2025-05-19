import os
import json
import logging
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.ERROR)

client = OpenAI()

system_instruction = "You are CarbonSustainAI, the voice of CarbonSustain — a climate-smart, data-driven guide helping small and mid-sized businesses (SMBs) track, reduce, and offset their carbon emissions using AI-powered insights and on-chain transparency."

class TweetLLM:
    

    def generate(self, factual_tweet: str, rant_tweet: str, max_tokens: int = 100, temperature: float = 0.7):
        # Use a4.py to find relevant tweets based on the factual tweet and company section
        a4_tweets_context = ""
        a4_section_context = "" # Initialize variable for company section context
        a4=None

        # --- Import a4.py and get relevant contexts ---
        try:
            # Try direct import first
            import a4
        except ImportError:
            try:
                # If direct import fails, try relative import
                from . import a4
            except ImportError:
                # If both imports fail, log error and continue without a4 context
                logging.error("Could not import a4.py. Ensure it is in the same directory as openai_inference.py and the application is run as a package.")
                a4 = None # Ensure a4 is None if import fails
            except Exception as e:
                # Catch any other exceptions during relative import attempt
                logging.error("An unexpected error occurred during relative import of a4.py: %s", e)
                a4 = None
        except Exception as e:
             # Catch any other exceptions during direct import attempt
            logging.error("An unexpected error occurred during direct import of a4.py: %s", e)
            a4 = None

        if a4:
            try:
                # Get relevant tweets
                relevant_tweets_from_a4 = a4.top3_matches(factual_tweet)
                a4_tweets_text = [tweet for tweet, score in relevant_tweets_from_a4]
                if a4_tweets_text:
                    # Label these tweets clearly as the reference/additional context
                    a4_tweets_context = "\n--- Relevant tweets from knowledge base (serving as reference context) ---\n" + "\n---\n".join(a4_tweets_text) + "\n--------------------------------------------------------------------\n\n"

                # Get the best section from company docs
                relevant_section, section_score = a4.best_section(factual_tweet)
                if relevant_section:
                    a4_section_context = (
                        f"\n--- Relevant section from company documents (potentially useful for integrating company objectives/products based on similarity score) ---\n"
                        f"Similarity Score: {section_score:.3f}\n\n"
                        f"{relevant_section}\n"
                        f"---------------------------------------------------------------------\n\n"
                    )
                if a4_tweets_context:
                    print(a4_tweets_context)
                if a4_section_context:
                    print(a4_section_context)

            except Exception as e:
                logging.error("Error using a4.py functions (top3_matches or best_section): %s", e)
                a4_tweets_context = ""
                a4_section_context = ""
        # --- End Import and Context Retrieval ---

        full_prompt_text = (
            "You will be provided with a factual tweet, a rant tweet, and several relevant tweets from a knowledge base (serving as reference context).\n\n"
            "You may also be provided with a relevant section from company documents.\n\n"
            "🎯 Your task:\n\n"
            "Fuse the truth from the factual tweet with the emotion or urgency of the rant tweet.\n\n"
            "Use the relevant tweets from the knowledge base to anchor your tone and viewpoint — calm, clear, constructive, reflecting CarbonSustain's voice.\n\n"
            "Optionally use the relevant company document section and its similarity score to help integrate company objectives or product mentions, maintaining the CarbonSustain voice.\n\n"
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
            "Relevant section from company documents (potentially useful for integrating company objectives/products based on similarity score):" # Added example section description
            "Similarity Score: 0.85\n\n" # Added example score
            "CarbonSustain offers AI-powered tools for granular Scope 3 tracking across complex supply chains, enabling SMBs to identify emission hotspots and engage suppliers for collaborative reduction efforts.\n\n" # Added example section content
            "✨ Example Output Tweet:\n"
            "\"Scope 3 sounds like a nightmare. But it's really a flashlight. You can't shrink what you can't see. Start with what you can track—your vendors, commutes, cloud usage. Visibility is power. #CarbonAccounting\"\n\n"
            "--- Now generate a tweet based on the following inputs ---\n\n"
            f"Factual Tweet: \"{factual_tweet}\"\n\n"
            f"Rant Tweet: \"{rant_tweet}\"\n\n"
            f"{a4_tweets_context}" # Include the relevant tweets from a4.py as reference context
            f"{a4_section_context}" # Include the relevant section from company docs
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
