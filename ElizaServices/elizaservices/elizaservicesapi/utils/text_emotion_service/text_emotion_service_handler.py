import boto3
from django.conf import settings

class TextEmotionService:
    def __init__(self):
        self.comprehend_client = boto3.client(
            'comprehend',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )

    def analyze_emotions(self, text, top_k=5):
        try:
            response = self.comprehend_client.detect_sentiment(
                Text=text,
                LanguageCode='en'
            )

            sentiment = response.get('Sentiment')
            scores = response.get('SentimentScore', {})

            # Convert AWS style to emotion format
            emotions = [
                {"emotion": "positive", "score": round(scores.get("Positive", 0.0), 4)},
                {"emotion": "negative", "score": round(scores.get("Negative", 0.0), 4)},
                {"emotion": "neutral", "score": round(scores.get("Neutral", 0.0), 4)},
                {"emotion": "mixed", "score": round(scores.get("Mixed", 0.0), 4)}
            ]

            # Sort by score descending and take top_k
            emotions_sorted = sorted(emotions, key=lambda x: x['score'], reverse=True)[:top_k]
            print(emotions_sorted)

            return {
                "emotions": emotions_sorted
            }
        except Exception as e:
            # Return neutral emotions in case of error
            print(e)
            return {
                "emotions": [
                    {"emotion": "neutral", "score": 1.0}
                ]
            } 