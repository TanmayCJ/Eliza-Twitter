import requests

class ExternalAPIClient:
    @staticmethod
    def call_api(url, tweet):
        try:
            response = requests.post(url, json={'text': tweet})
            data = response.json()
            if isinstance(data, dict) and 'is_appropriate' in data:
                return ('approved' if data.get('is_appropriate') else 'rejected'), data
            if isinstance(data, dict) and 'predicted_score' in data:
                score = data.get('predicted_score', 0)
                return ('approved' if score >= 5.0 else 'rejected'), data
            if isinstance(data, dict) and 'score' in data:
                score = data.get('score', 0)
                return ('approved' if score >= 0.6 else 'rejected'), data
            return (data.get('status', 'rejected'), data)
        except Exception as e:
            return ('rejected', {'error': str(e)})
