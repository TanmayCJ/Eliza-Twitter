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
                    # Adjusted formatting to be clearer in the prompt
                    a4_tweets_context = "\nReference Tweets (from knowledge base):\n" + "\n".join([f"• {tweet}" for tweet in a4_tweets_text]) + "\n\n"

                # Get the best section from company docs
                relevant_section, section_score = a4.best_section(factual_tweet)
                if relevant_section:
                    # Adjusted formatting to be clearer in the prompt
                    a4_section_context = (
                        f"Relevant section ({section_score:.2f}):\n" # Using score format from example
                        f"{relevant_section}\n\n"
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

        # Construct the full prompt string for the user message
        # Adjusted prompt structure for clarity for the model
        full_prompt_text = (
            "You are CarbonSustainAI, the voice of CarbonSustain — a climate-smart, data-driven guide helping small and mid-sized businesses (SMBs) track, reduce, and offset their carbon emissions using AI-powered insights and on-chain transparency.\n\n" # Repeat persona here
            "🎯 Your task:\n"
            "Fuse the truth from the factual tweet with the emotion or urgency of the rant tweet.\n"
            "Use the relevant tweets from the knowledge base to anchor your tone and viewpoint—calm, clear, constructive, reflecting CarbonSustain's voice.\n\n"
            "Company integration rule:\n"
            " • If a relevant company document section is provided with a similarity score ≥ 0.8, **strongly consider** logically and relevantly weaving in **CarbonSustain's name**, mission, or a relevant product/philosophy (e.g., measurement, AI, supply-chain visibility) based on the factual tweet, rant tweet, and relevant contexts. Keep it brief and advisory—never salesy.\n"
            " • If the similarity score < 0.8 or no section is provided, omit any direct company reference.\n\n"
            "Write a single, original tweet in CarbonSustain's voice that:\n"
            " - Acknowledges frustration or irony.\n"
            " - Reframes the issue with insight and optimism.\n"
            " - Offers a solution, mindset shift, or practical action.\n"
            " - Optionally mentions CarbonSustain's name, philosophy, or tools, **prioritizing logical and relevant integration** when permitted by the rule above.\n"
            " - Ends with a strong closer—a mic drop, hopeful insight, or hashtag.\n\n"
            "🧠 Tone & Style:\n"
            " Calm, clear, slightly witty.\n"
            " Feels like a climate‑smart advisor, not a corporate brochure.\n"
            " Never panicked. Never preachy. Never doomscroll bait.\n\n"
            "📝 Writing Rules:\n"
            " 1–3 lines max. No threads.\n"
            " Be informative and emotionally aware.\n"
            " Mix activist sharpness with solution‑focused clarity.\n"
            " Tweet must be 280 characters or less. Do not cut off abruptly.\n\n"
            "--- Generate a tweet based on the following inputs ---"
            "\n✨ Output Tweet:\n"
            f"Factual Tweet: \"{factual_tweet}\"\n"
            f"Rant Tweet: \"{rant_tweet}\"\n"
            f"{a4_tweets_context}"
            f"{a4_section_context}"

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
            generated = response.choices[0].message.content.strip() # Add strip() to remove leading/trailing whitespace

        except Exception as e:
            logging.error("Error generating tweet with OpenAI: %s", e)
            generated = "An error occurred while generating the tweet. Please try again."

        print(generated)
        return generated
