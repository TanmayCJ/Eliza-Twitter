import requests

# For popularity score
response = requests.post(
    "http://127.0.0.1:8000/api/popularity/", 
    json={"text": "Your tweet text here"}
)
print(response.json())

# For safety score
response = requests.post(
    "http://127.0.0.1:8000/api/safety/", 
    json={"text": "Your tweet text here"}
)
print(response.json())