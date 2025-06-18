import os
import json
import logging
from openai import OpenAI
from dotenv import load_dotenv
import random
from . import semantic_retriever
load_dotenv()

logging.basicConfig(level=logging.ERROR)

client = OpenAI()

system_instruction = "You are CarbonSustainAI, the voice of CarbonSustain — a climate-smart, data-driven guide helping small and mid-sized businesses (SMBs) track, reduce, and offset their carbon emissions using AI-powered insights and on-chain transparency."

class TweetLLM:
    

    def generate(self, factual_tweet: str, rant_tweet: str, max_tokens: int = 100, temperature: float = 0.7):
        # Use semantic_retriever.py to find relevant tweets based on the factual tweet and company section
        tweets_context = ""
        section_context = ""
        section_score = 0

        try:
            # Get relevant tweets
            relevant_tweets = semantic_retriever.top3_matches(factual_tweet)
            tweets_text = [tweet for tweet, score in relevant_tweets]
            if tweets_text:
                tweets_context = "\n--- Relevant tweets from knowledge base (serving as reference context) ---\n" + "\n---\n".join(tweets_text) + "\n--------------------------------------------------------------------\n\n"

            relevant_section, score = semantic_retriever.best_section(factual_tweet)
            section_score = score
            if relevant_section:
                section_context = (
                    f"\n--- Relevant section from company documents (potentially useful for integrating company objectives/products based on similarity score) ---\n"
                    f"Similarity Score: {section_score:.3f}\n\n"
                    f"{relevant_section}\n"
                    f"---------------------------------------------------------------------\n\n"
                )

            if tweets_context:
                print(tweets_context)
            if section_context:
                print(section_context)

        except Exception as e:
            logging.error("Error using semantic_retriever functions (top3_matches or best_section): %s", e)
            tweets_context = ""
            section_context = ""
            section_score = 0

        value = round(random.random(), 2)
        print("random value is", value)

        # Conditionally build the company integration rules and section block
        company_integration_rules = ""
        additional_rules = ""
        section_block = ""
        if value <= 0.25 and section_context:
            print("true section")
            company_integration_rules = (
                "Company Integration Rules\n"
                "• **STRICT RULE: You ABSOLUTELY MUST integrate a mention of CarbonSustain's name, mission, philosophy, or product area IF** a relevant company document section is provided **.\n"
                "• **IF** the condition above is met (section provided **AND** ), then **seamlessly and logically** weave in a relevant mention (e.g., AI insights, emissions measurement, supply chain transparency).\n"
                "• The mention **must be directly supported by the content of the PROVIDED relevant section and its score**.\n"
                "• Keep mentions brief, natural, and advisory — never promotional or salesy.\n\n"
            )
            section_block = section_context
            additional_rules = (
                "• Only mention carbonsustain - and then in a single, lightly boastful sentence - if proposing a solution, announcing an initiative, partnership, tool, or responding as the company\n"
                "• That boast line should briefly state how carbonsustain is helping, innovating, or supporting the cause\n"
                "• Do NOT mention carbonsustain in purely observational, critical, or third-party contexts\n"
            )
        else:
            print("false section")

        # Single prompt template
        full_prompt_text = f"""
            You are CarbonSustainAI — the voice of CarbonSustain: a climate-smart, data-first guide helping small and mid-sized businesses (SMBs) track, reduce, and offset their carbon emissions through AI-powered insights and on-chain accountability.

            Your Mission
            You are given:

            A factual tweet from @CarbonTruth (serious, data-heavy)

            A rant tweet from @CarbonRant (sarcastic, emotional, or critical)

            A context block of CarbonSustain tweets that define the company's tone, phrasing, and viewpoint ({'present' if tweets_context else 'not present'})

            A relevant section from company documents, with a similarity score and product details ({'present' if section_context else 'not present'})

            Your job is to generate a single, original tweet that:

            Fuses the credibility of the factual tweet with the emotion or urgency of the rant

            Mirrors the tone, vocabulary, and phrasing of real CarbonSustain tweets (when provided) to stay on-brand

            Reflects CarbonSustain's calm, constructive worldview

            {company_integration_rules}
            IMPORTANT GUIDELINES:
            • Always start with a clear fact, stat, or policy observation
            • Keep tweets to 1-2 sentences, 0-2 emojis (🌍 🚀 ✅), and 1-2 relevant hashtags
            • Use a rhetorical question or call-to-action in ~25% of tweets
            {additional_rules}
            You must always use and blend both the factual tweet and the rant tweet in your output. Do not ignore or omit either. The final tweet should gracefully and clearly reflect the content and tone of both.
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
            {tweets_context}{section_block}

            ✨ Output Tweet:
        """

        try:
            print(full_prompt_text)
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
