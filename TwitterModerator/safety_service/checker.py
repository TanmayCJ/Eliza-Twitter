from detoxify import Detoxify

class SafetyChecker:
    def __init__(self):
        self.model = Detoxify("unbiased")

    def predict(self, text: str) -> dict:
        results = self.model.predict(text)
        is_appropriate = results.get("toxicity", 1.0) < 0.5
        return {
            "is_appropriate": is_appropriate,
            "scores": results,
            "explanation": "Safety evaluation based on Detoxify model."
        }