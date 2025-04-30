from transformers import pipeline
import re

class SafetyChecker:
    def __init__(self):
        self.classifier = None  # will hold the HF pipeline

    def load_model(self):
        if self.classifier is None:
            try:
                # download & cache the “unitary/toxic-bert” model once
                self.classifier = pipeline(
                    "text-classification",
                    model="unitary/toxic-bert",
                    return_all_scores=True
                )
            except Exception as e:
                print(f"Error loading Toxic-BERT pipeline: {e}")
                self.classifier = None

    def clean_text(self, text: str) -> str:
        text = str(text)
        text = re.sub(r"http\S+|www\S+", "", text)
        text = re.sub(r"@\w+", "", text)
        text = re.sub(r"\n", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def predict(self, text: str) -> dict:
        self.load_model()
        cleaned = self.clean_text(text)

        if self.classifier is None:
            return {
                "is_appropriate": True,
                "scores": {},
                "explanation": "Toxic-BERT model could not be loaded.",
                "cleaned_text": cleaned
            }

        # run the classifier
        out = self.classifier(cleaned)[0]  
        # out is a list of dicts: [{label: "toxic", score: 0.12}, …]
        scores = {d["label"]: d["score"] for d in out}
        is_safe = scores.get("toxic", 1.0) < 0.5

        return {
            "is_appropriate": is_safe,
            "scores": scores,
            "explanation": "Safety evaluation via unitary/toxic-bert.",
            "cleaned_text": cleaned
        }
