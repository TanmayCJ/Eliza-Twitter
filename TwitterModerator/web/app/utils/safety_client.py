import requests

def get_safety_score(text):
    url = "http://safety:9002/predict"
    resp = requests.post(url, json={"text": text})
    resp.raise_for_status()
    return resp.json()

def get_image_safety_score(image_file):
    url = "http://safety:9002/image_check"
    files = {'image': image_file}
    resp = requests.post(url, files=files)
    resp.raise_for_status()
    return resp.json()