import requests
import json
import re
import textwrap
import time
from django.conf import settings

class NewsService:
    def __init__(self, api_key, countries=None, max_retries=1, retry_delay=1.0):
        
        self.api_key = settings.OPENAI_API_KEY
        self.countries = countries or ["US", "CA"]
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.url = "https://api.openai.com/v1/responses"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def fetch_environmental_news(self):
        user_prompt = textwrap.dedent(f"""
            Search and compile the 10 latest news (preferably within the last 10 days) related to:
            - Environmental issues (e.g., climate change, conservation, pollution control)
            - Sustainability (renewable energy, eco-initiatives)
            - Conservation (wildlife, forests, oceans)
            - Environmental activism and climate policies

            STRICTLY include only news from these countries: {', '.join(self.countries)}.

            Return a JSON object in this format:
            {{
              "news": [
                {{
                  "title": "...",
                  "date": "YYYY-MM-DD",
                  "location": "...",
                  "summary": "...",
                  "url": "https://..."
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
                    continue

                parsed_response = response.json()

                # Extract assistant message content
                content_blocks = parsed_response['output'][1]['content']
                raw_output_text = ""
                for block in content_blocks:
                    if block['type'] == 'output_text':
                        raw_output_text = block['text']
                        break

                # Strip ```json ... ``` or fallback to raw
                match = re.search(r'```json\s*(.*?)\s*```', raw_output_text, re.DOTALL)
                clean_json_str = match.group(1) if match else raw_output_text

                news_data = json.loads(clean_json_str)
                return news_data

            except json.JSONDecodeError:
                return {"news": []}

            except Exception:
                pass

            if attempt < self.max_retries:
                time.sleep(self.retry_delay)

        return {"news": []}
