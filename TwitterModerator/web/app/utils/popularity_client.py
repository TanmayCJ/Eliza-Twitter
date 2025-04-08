import requests

def get_popularity_score(text):
    url = "http://popularity:9001/predict"
    resp = requests.post(url, json={"text": text})
    resp.raise_for_status()
    return resp.json()