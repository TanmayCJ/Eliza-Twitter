import re
from urllib.parse import urlparse
import validators

class URLProcessor:
    @staticmethod
    def extract_urls(text):
        if not text:
            return "", []
        url_pattern = re.compile(r'(https?://[^\s\'"]+|www\.[^\s\'"]+)')
        urls = url_pattern.findall(text)
        text_without_urls = url_pattern.sub('', text).strip()
        valid_urls = []
        for url in urls:
            try:
                url = url.rstrip('.,;:!?)"\'')
                if url.startswith('www.') and not url.startswith('http'):
                    url = 'http://' + url
                parsed = urlparse(url)
                if parsed.netloc:
                    valid_urls.append(url)
            except Exception:
                pass
        return text_without_urls, valid_urls

    @staticmethod
    def append_urls_to_text(text, urls, char_limit=1000):
        if not urls:
            return text
        result = text.strip()
        for url in sorted(urls, key=len):
            if validators.url(url) and len(result) + len(url) + 1 <= char_limit:
                result += ' ' + url
        return result
