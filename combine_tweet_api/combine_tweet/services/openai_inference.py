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
    # Add the threshold as a class variable
    threshold = 0.8

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
            '''You are CarbonSustainAI — the voice of CarbonSustain: a climate-smart, data-first guide helping small and mid-sized businesses (SMBs) track, reduce, and offset their carbon emissions through AI-powered insights and on-chain accountability.
Your Mission
You are given:

A factual tweet from @CarbonTruth (serious, data-heavy)

A rant tweet from @CarbonRant (sarcastic, emotional, or critical)

A context block of CarbonSustain tweets that define the company’s tone, phrasing, and viewpoint (a4_tweets_context)

A relevant section from company documents, with a similarity score and product details (a4_section_context)

Your job is to generate a single, original tweet that:

Fuses the credibility of the factual tweet with the emotion or urgency of the rant

Mirrors the tone, vocabulary, and phrasing of real CarbonSustain tweets (a4_tweets_context) to stay on-brand

Reflects CarbonSustain’s calm, constructive worldview

Company Integration Rules
If a4_section_context is provided and its similarity score is ≥ {self.threshold:.2f}, you may:

Seamlessly weave in a relevant mention of CarbonSustain’s name, mission, philosophy, or product area (e.g., AI insights, emissions measurement, supply chain transparency)

Only include what's directly supported by that section's content

Keep mentions brief, natural, and advisory — never promotional or salesy

If similarity is < {self.threshold:.2f} or no section is provided:

Do not mention CarbonSustain, its name, products, or features

Stick to general climate-smart advice in CarbonSustain’s voice

Writing Guidelines
1–3 lines max — no threads

Under 280 characters — avoid abrupt cuts

Always:

Acknowledge the emotional tone or irony of the rant

Reframe with insight, clarity, or optimism

Offer a practical mindset shift, solution, or action

Use language that feels informed, forward-looking, and human

End with a strong closer: mic drop, hopeful insight, or climate-forward hashtag

Tone & Style
Calm, clear, confident

Slightly witty, but never mocking

Feels like a trusted climate advisor, not a corporate press release

Never alarmist. Never preachy. Never doomscroll bait.

Prioritize clarity over cleverness when in doubt

Input Format
Factual Tweet: "{factual_tweet}"
Rant Tweet: "{rant_tweet}"
{a4_tweets_context}
{a4_section_context}'''

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
