# **Climate Tweet Combiner API**

A Django-based API that generates and evaluates climate-related tweets by blending factual and rant-style content. It uses large language models (OpenAI GPT or Gemini) to create a tweet from a factual and rant-style input, checks it for safety and popularity using external APIs, and stores the results in a database. The API also processes embedded URLs and exposes endpoints to generate and retrieve tweets.

## **How It Works**

1. **Data Sources**  
   - Pulls the latest factual tweet from CarbonTruth and the latest rant tweet from CarbonRant in the database.

2. **Tweet Generation**  
   - Combines the two tweets using a prompt template and sends it to a configured LLM to generate a new tweet.

3. **Safety & Popularity Checks**  
   - Evaluates the generated tweet using safety and popularity APIs.  
   - If it fails, the system retries with a revised prompt until it passes or hits a retry limit.

4. **Result Storage**  
   - Stores the final tweet, original inputs, safety and popularity scores, and any extracted URLs in the database.

5. **API Endpoints**  
   - Offers endpoints for generating tweets (GET/POST) and fetching stored tweet data.

## **Setup Instructions**


# 1. Navigate to combine_tweet_api folder
cd carbontruth/combine_tweet_api

# 2. Create a virtual environment
python -m venv venv

# 3. Activate the virtual environment
```bash
# On Windows
elizaservicevenv\Scripts\activate
# On macOS/Linux
source elizaservicevenv/bin/activate
```

# 4. Install dependencies
pip install -r requirements.txt



# 5. Set up the database
- python manage.py makemigrations
- python manage.py migrate combine_tweet --fake-initial

# 7. Run the development server
- python manage.py runserver

# Test it on Postman using the api endpoint
- `POST /generate-combined`
