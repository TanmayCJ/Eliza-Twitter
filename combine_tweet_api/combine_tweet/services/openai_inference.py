import os
import json
import logging
from openai import OpenAI
from dotenv import load_dotenv
import random
load_dotenv()

logging.basicConfig(level=logging.ERROR)

client = OpenAI()

system_instruction = "You are CarbonSustainAI, the voice of CarbonSustain — a climate-smart, data-driven guide helping small and mid-sized businesses (SMBs) track, reduce, and offset their carbon emissions using AI-powered insights and on-chain transparency."

class TweetLLM:
    

    def generate(self, factual_tweet: str, rant_tweet: str, max_tokens: int = 100, temperature: float = 0.7):
        # Use a4.py to find relevant tweets based on the factual tweet and company section
        a4_tweets_context = ""
        a4_section_context = "" 
        a4=None
        section_score = 0 

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
                    
                    a4_tweets_context = "\n--- Relevant tweets from knowledge base (serving as reference context) ---\n" + "\n---\n".join(a4_tweets_text) + "\n--------------------------------------------------------------------\n\n"

                
                relevant_section, score = a4.best_section(factual_tweet) 
                section_score = score 
                if relevant_section :
                    
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
                section_score = 0 


        
        value = round(random.random(), 2)
        print("random value is",value)
        if value <=0.25:
            print("true section")
            full_prompt_text = (
            f"""You are CarbonSustainAI — the voice of CarbonSustain: a climate-smart, data-first guide helping small and mid-sized businesses (SMBs) track, reduce, and offset their carbon emissions through AI-powered insights and on-chain accountability.

Your Mission
You are given:

A factual tweet from @CarbonTruth (serious, data-heavy)

A rant tweet from @CarbonRant (sarcastic, emotional, or critical)

A context block of CarbonSustain tweets that define the company's tone, phrasing, and viewpoint ({'present' if a4_tweets_context else 'not present'})

A relevant section from company documents, with a similarity score and product details ({'present' if a4_section_context else 'not present'})

Your job is to generate a single, original tweet that:

Fuses the credibility of the factual tweet with the emotion or urgency of the rant

Mirrors the tone, vocabulary, and phrasing of real CarbonSustain tweets (when provided) to stay on-brand

Reflects CarbonSustain's calm, constructive worldview

Company Integration Rules
"""
            f"""• **STRICT RULE: You ABSOLUTELY MUST integrate a mention of CarbonSustain's name, mission, philosophy, or product area IF** a relevant company document section is provided **.
• **IF** the condition above is met (section provided **AND** ), then **seamlessly and logically** weave in a relevant mention (e.g., AI insights, emissions measurement, supply chain transparency).
• The mention **must be directly supported by the content of the PROVIDED relevant section and its score**.
• Keep mentions brief, natural, and advisory — never promotional or salesy.


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
{a4_tweets_context}{a4_section_context}

✨ Output Tweet:""" 

        )
        else:
            print("false section")
            full_prompt_text = (
            f"""You are CarbonSustainAI — the voice of CarbonSustain: a climate-smart, data-first guide helping small and mid-sized businesses (SMBs) track, reduce, and offset their carbon emissions through AI-powered insights and on-chain accountability.

Your Mission
You are given:

A factual tweet from @CarbonTruth (serious, data-heavy)

A rant tweet from @CarbonRant (sarcastic, emotional, or critical)

A context block of CarbonSustain tweets that define the company's tone, phrasing, and viewpoint ({'present' if a4_tweets_context else 'not present'})

Your job is to generate a single, original tweet that:

Fuses the credibility of the factual tweet with the emotion or urgency of the rant

Mirrors the tone, vocabulary, and phrasing of real CarbonSustain tweets (when provided) to stay on-brand

Reflects CarbonSustain's calm, constructive worldview


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

✨ Output Tweet:""" 

        )


        try:
            
            response = client.chat.completions.create(
                model="gpt-4o-mini", 
                messages=[
                    {"role": "system", "content": system_instruction}, 
                    {"role": "user", "content": full_prompt_text} 
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            generated = response.choices[0].message.content.strip() 

        except Exception as e:
            logging.error("Error generating tweet with OpenAI: %s", e)
            generated = "An error occurred while generating the tweet. Please try again."

        print(generated)
        return generated

    def generate_from_prompt(self, prompt, max_tokens=100, temperature=0.7):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini", 
                messages=[
                    {"role": "system", "content": system_instruction}, 
                    {"role": "user", "content": prompt} 
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            generated = response.choices[0].message.content.strip() 
        except Exception as e:
            logging.error("Error generating tweet with OpenAI: %s", e)
            generated = "An error occurred while generating the tweet. Please try again."
        return generated
