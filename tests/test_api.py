import requests

url = "http://127.0.0.1:5001/analyze"

data = {
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}

response = requests.post(url, json=data)

print("STATUS:", response.status_code)
print("RESPONSE:", response.text)