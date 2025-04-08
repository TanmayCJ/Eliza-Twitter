import re
import torch
import torch.nn as nn
from sentence_transformers import SentenceTransformer
import pickle

# Same architecture as in training
class PopularityRegressor(nn.Module):
    def __init__(self):
        super().__init__()
        self.model = nn.Sequential(
            nn.Linear(384, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 1)
        )

    def forward(self, x):
        return self.model(x)

class PopularityPredictor:
    def __init__(self, model_path: str, scaler_path: str):
        # Load device and model
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.regressor = PopularityRegressor().to(self.device)
        self.regressor.load_state_dict(torch.load(model_path, map_location=self.device))
        self.regressor.eval()

        # Load the scaler for consistent transformations
        with open(scaler_path, "rb") as f:
            self.scaler = pickle.load(f)

        # Load the SentenceTransformer for embeddings
        self.embed_model = SentenceTransformer("all-MiniLM-L6-v2")

    def clean_text(self, text: str) -> str:
        """Basic cleanup for tweet text."""
        text = str(text)
        text = re.sub(r"http\S+|www\S+", "", text)
        text = re.sub(r"@\w+", "", text)
        text = re.sub(r"\n", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def predict(self, tweet: str) -> dict:
        """Return predicted popularity score for a tweet."""
        cleaned = self.clean_text(tweet)
        embedding = self.embed_model.encode([cleaned])
        X_tensor = torch.tensor(embedding, dtype=torch.float32).to(self.device)

        with torch.no_grad():
            predicted_score = self.regressor(X_tensor).item()

        # Ensure the score is within the desired [0, 100] range.
        predicted_score = max(0, min(100, predicted_score))

        return {
            "predicted_score": predicted_score,
            "explanation": "Predicted popularity score using neural net and SentenceTransformer embeddings, standardized to [0, 100]."
        }