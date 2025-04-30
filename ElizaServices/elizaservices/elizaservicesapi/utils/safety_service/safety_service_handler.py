from .safety_bot import SafetyChecker

class SafetyService:
    def __init__(self):
        self.checker = SafetyChecker()

    def check_text_safety(self, text: str) -> dict:
        return self.checker.predict(text)

    def check_image_labels(self, labels: list) -> dict:
        pass
        