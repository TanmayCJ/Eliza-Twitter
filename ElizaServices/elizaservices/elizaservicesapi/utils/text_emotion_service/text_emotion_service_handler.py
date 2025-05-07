import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification

class TextEmotionService:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained("monologg/bert-base-cased-goemotions-original")
        self.model = AutoModelForSequenceClassification.from_pretrained("monologg/bert-base-cased-goemotions-original")
        self.goemotion_labels = [
            "admiration", "amusement", "anger", "annoyance", "approval", "caring",
            "confusion", "curiosity", "desire", "disappointment", "disapproval", "disgust",
            "embarrassment", "excitement", "fear", "gratitude", "grief", "joy", "love",
            "nervousness", "optimism", "pride", "realization", "relief", "remorse",
            "sadness", "surprise", "neutral"
        ]

    def analyze_emotions(self, text, top_k=5):
        # Tokenize and pass through model
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True)
        outputs = self.model(**inputs)

        # Apply softmax to get probabilities
        probs = F.softmax(outputs.logits, dim=1)

        # Get top emotions
        topk = torch.topk(probs, k=top_k)
        top_emotions = [(self.goemotion_labels[idx], float(score)) for idx, score in zip(topk.indices[0], topk.values[0])]

        return {
            "emotions": [{"emotion": label, "score": score} for label, score in top_emotions]
        } 