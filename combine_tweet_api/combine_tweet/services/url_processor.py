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
        
        # Make sure text is properly stripped
        result = text.strip()
        
        # Ensure we don't already have these URLs in the text
        for url in urls:
            if url in result:
                urls.remove(url)
                
        # If no URLs left to add, return the text as is
        if not urls:
            return result
            
        # Sort URLs by length to prioritize shorter URLs
        sorted_urls = sorted(urls, key=len)
        
        # Try to add URLs while respecting the character limit
        for url in sorted_urls:
            # Handle URL validation more safely
            try:
                is_valid = validators.url(url)
            except:
                # If validation fails, assume it's valid to ensure URLs are included
                is_valid = True
                
            if is_valid and len(result) + len(url) + 1 <= char_limit:
                result += ' ' + url
                
        return result
