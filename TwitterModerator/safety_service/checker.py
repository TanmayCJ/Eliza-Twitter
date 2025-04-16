from detoxify import Detoxify
import re

class SafetyChecker:
    def __init__(self):
        self.model = Detoxify("unbiased")

    def clean_text(self, text: str) -> str:
        """Basic cleanup for tweet text."""
        text = str(text)
        text = re.sub(r"http\S+|www\S+", "", text)
        text = re.sub(r"@\w+", "", text)
        text = re.sub(r"\n", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def predict(self, text: str) -> dict:
        cleaned_text = self.clean_text(text)
        results = self.model.predict(cleaned_text)
        is_appropriate = results.get("toxicity", 1.0) < 0.5
        return {
            "is_appropriate": is_appropriate,
            "scores": results,
            "explanation": "Safety evaluation based on Detoxify model.",
            "cleaned_text": cleaned_text
        }