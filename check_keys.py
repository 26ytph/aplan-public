import os, sys, requests, time
from dotenv import load_dotenv

load_dotenv()

keys = []
for i in range(1, 8):
    k = os.getenv(f"GEMINI_API_KEY_{i}")
    if k:
        keys.append(k)

print(f"✅ 找到 {len(keys)} 把金鑰，開始逐一測試回血狀況...")

payload = {
    "model": "models/gemini-embedding-001",
    "content": {"parts": [{"text": "ping"}]}
}

for idx, key in enumerate(keys, 1):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={key}"
    resp = requests.post(url, json=payload)
    if resp.status_code == 200:
        print(f"  🟢 Key {idx} ({key[:10]}...): 額度健康 (Status 200)")
    else:
        print(f"  🔴 Key {idx} ({key[:10]}...): 尚未回血 ({resp.status_code}) -> {resp.text[:50]}...")
    time.sleep(1) # 避免打同一個 Project 太快觸發 RPM
