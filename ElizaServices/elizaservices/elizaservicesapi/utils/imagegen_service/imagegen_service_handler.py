import requests
from django.conf import settings

class ImageGenServiceHandler:
    def __init__(self):
        self.api_key = settings.PEXEL_API_KEY
        self.base_url_template = settings.PEXEL_API_BASE_URL  

    def fetch_image(self, keyword):
        """
        Given a keyword, returns a relevant image URL from Pexels or "NO_IMAGE".
        """
        if not self.api_key or not keyword:
            return "NO_IMAGE"

        # Replace {keyword} with actual search term
        url = self.base_url_template.replace("{keyword}", keyword)

        headers = {"Authorization": self.api_key}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            if data.get("photos"):
                return data["photos"][0]["src"]["original"]
        return "NO_IMAGE"

