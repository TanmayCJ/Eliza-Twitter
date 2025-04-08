import requests

def get_safety_score(text):
    url = "http://safety:9002/predict"
    resp = requests.post(url, json={"text": text})
    resp.raise_for_status()
    return resp.json()