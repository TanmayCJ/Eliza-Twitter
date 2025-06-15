import requests
import json
import re
import textwrap
import time
from django.conf import settings
from ..text_emotion_service.text_emotion_service_handler import TextEmotionService
from ..personality_service.personality_service_handler import PersonalityServiceHandler

class NewsService:
    def __init__(self, api_key, countries=None, max_retries=1, retry_delay=1.0):
        self.api_key = settings.OPENAI_API_KEY
        self.countries = countries or ["US", "CA"]
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.url = settings.OPENAI_API_BASE_URL_V1
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        self.text_emotion_service = TextEmotionService()
        self.personality_service = PersonalityServiceHandler()

    def fetch_environmental_news(self):
        user_prompt = textwrap.dedent(f"""
            Search and compile the 5 latest news (exactlywithin the last 10 days) related to:
            - Environmental issues (e.g., climate change, conservation, pollution control)
            - Sustainability (renewable energy, eco-initiatives)
            - Conservation (wildlife, forests, oceans)
            - Environmental activism and climate policies

            STRICTLY include only news from these countries: {', '.join(self.countries)}.

            For each news article, include the following fields:
            - "title": A short, clear headline.
            - "date": Date in YYYY-MM-DD format.
            - "location": Where the news took place.
            - "summary": 2–3 sentence explanation of the news.
            - "url": A direct link to the news source.
            - "event_type": Classify the news type — examples: "disaster", "hypocrisy", "small win", "corporate scandal", "activism", "policy".

            Return a JSON object strictly in this format:
            {{
              "news": [
                {{
                  "title": "...",
                  "date": "YYYY-MM-DD",
                  "location": "...",
                  "summary": "...",
                  "url": "https://...",
                  "event_type": "..."
                }}
              ]
            }}
        """)

        payload = {
            "model": "gpt-4o",
            "input": [
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": "\n"}]
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": user_prompt}]
                }
            ],
            "text": {"format": {"type": "text"}},
            "reasoning": {},
            "tools": [
                {
                    "type": "web_search_preview",
                    "user_location": {"type": "approximate", "country": "US"},
                    "search_context_size": "medium"
                }
            ],
            "temperature": 0.7,
            "max_output_tokens": 2048,
            "top_p": 1,
            "store": True
        }

        for attempt in range(self.max_retries):
            try:
                response = requests.post(self.url, headers=self.headers, data=json.dumps(payload))

                if response.status_code != 200:
                    try:
                        error_message = response.text
                    except Exception:
                        error_message = "<Could not retrieve response text>"
                    print(f"[NewsService] Attempt {attempt+1}: Received non-200 status code: {response.status_code}. Response message: {error_message}. Retrying...")
                    continue

                try:
                    parsed_response = response.json()
                except Exception as e:
                    print(f"[NewsService] Attempt {attempt+1}: Failed to parse JSON from response. Error: {e}. Response text: {response.text}")
                    continue

                # Extract assistant message content
                try:
                    content_blocks = parsed_response['output'][1]['content']
                except Exception as e:
                    print(f"[NewsService] Attempt {attempt+1}: Could not extract content blocks from response JSON. Error: {e}. Full response: {parsed_response}")
                    continue

                raw_output_text = ""
                for block in content_blocks:
                    if block['type'] == 'output_text':
                        raw_output_text = block['text']
                        break

                # Strip ```json ... ``` or fallback to raw
                match = re.search(r'```json\s*(.*?)\s*```', raw_output_text, re.DOTALL)
                clean_json_str = match.group(1) if match else raw_output_text

                try:
                    news_data = json.loads(clean_json_str)
                except Exception as e:
                    print(f"[NewsService] Attempt {attempt+1}: Failed to parse news JSON. Error: {e}. Cleaned string: {clean_json_str}")
                    continue
                
                # Add emotion and personality analysis for each news item
                for news_item in news_data.get('news', []):
                    summary = news_item.get('summary', '')
                    if summary:
                        try:
                            # Get emotion analysis
                            emotion_analysis = self.text_emotion_service.analyze_emotions(summary, top_k=3)
                            news_item['emotions'] = emotion_analysis['emotions']
                            
                            # Get personality analysis based on emotions
                            personality_analysis = self.personality_service.analyze_personality(emotion_analysis['emotions'])
                            news_item['matched_personality'] = personality_analysis['matched_personality']
                        except Exception as e:
                            # Set default values in case of error
                            news_item['emotions'] = [{"emotion": "neutral", "score": 1.0}]
                            news_item['matched_personality'] = "Neil deGrasse Tyson"
                
                if not news_data.get('news'):
                    print("[NewsService] No news items found in the response. Returning empty news list.")

                return news_data

            except json.JSONDecodeError as e:
                print(f"[NewsService] JSONDecodeError: {e}. Returning empty news list.")
                return {"news": []}

            except Exception as e:
                print(f"[NewsService] Exception occurred: {e}. Retrying if attempts remain.")

            if attempt < self.max_retries:
                time.sleep(self.retry_delay)

        print("[NewsService] All attempts exhausted. Returning empty news list.")
        return {"news": []}
