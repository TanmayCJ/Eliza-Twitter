from typing import Dict, List

class PersonalityServiceHandler:
    def __init__(self):
        self.personality_emotions = {
            "Greta Thunberg": {"anger", "disapproval", "remorse", "fear", "sadness"},
            "Neil deGrasse Tyson": {"curiosity", "realization", "neutral", "approval", "confusion"},
            "George Carlin": {"anger", "disgust", "annoyance", "amusement", "surprise"},
            "Elon Musk": {"optimism", "curiosity", "surprise", "desire"},
            "Alexandria Ocasio-Cortez": {"pride", "anger", "excitement", "approval", "desire"},
            "David Attenborough": {"admiration", "gratitude", "joy", "relief", "love"},
            "The Caring Parent": {"caring", "grief", "nervousness", "disappointment", "embarrassment"}
        }
        self.THRESHOLD = 0.05

    def match_personality(self, emotions: List[Dict[str, float]]) -> str:
        # Filter emotions above threshold and sort by score
        emotion_scores = [(e["emotion"], e["score"]) for e in emotions if e["score"] >= self.THRESHOLD]
        emotion_scores.sort(key=lambda x: -x[1])
        top_emotions = [e[0] for e in emotion_scores[:5]]

        best_match = None
        max_matches = 0

        for personality, emotion_set in self.personality_emotions.items():
            match_count = sum(1 for emo in top_emotions if emo in emotion_set)
            if match_count > max_matches:
                best_match = personality
                max_matches = match_count
            elif match_count == max_matches and best_match is None:
                best_match = personality

        return best_match

    def analyze_personality(self, emotions: List[Dict[str, float]]) -> Dict:
        matched_personality = self.match_personality(emotions)
        return {
            "matched_personality": matched_personality,
            "emotions": emotions
        }
