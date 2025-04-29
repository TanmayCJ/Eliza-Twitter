from .image_bot import ImageCaptioner

class CaptionService:
    def __init__(self):
        self.captioner = ImageCaptioner()

    def generate_caption(self, image_file):
        return self.captioner.generate_caption(image_file)