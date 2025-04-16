import requests

def get_image_caption(image_file):
    url = "http://caption:9003/caption"
    files = {'image': image_file}
    response = requests.post(url, files=files)
    response.raise_for_status()
    return response.json()