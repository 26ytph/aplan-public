import os, sys, requests
from dotenv import load_dotenv

load_dotenv()
key1 = os.getenv("GEMINI_API_KEY_1")

if not key1:
    print("API Key 1 is empty!")
    sys.exit(1)

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={key1}"
payload = {
    "model": "models/gemini-embedding-001",
    "content": {
        "parts": [{"text": "Hello world"}]
    }
}

print(f"Testing Key 1: {key1[:15]}...")
resp = requests.post(url, json=payload)
print(f"Status Code: {resp.status_code}")
print(f"Response: {resp.text}")
