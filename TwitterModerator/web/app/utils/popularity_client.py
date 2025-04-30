import requests

def get_popularity_score(text):
    url = "http://popularity:9001/predict"
    resp = requests.post(url, json={"text": text})
    resp.raise_for_status()
    return resp.json()

def get_top_hashtags(text, hashtags, top_n):
    url = "http://popularity:9001/compare_hashtags"
    resp = requests.post(url, json={"text": text, "hashtags": hashtags, "top_n": top_n})
    resp.raise_for_status()
    return resp.json()