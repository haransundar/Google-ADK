import requests

url = "http://localhost:8002/api/v1/investigate"
try:
    resp = requests.post(url, json={"query": "test"}, stream=True, timeout=10)
    print("Status:", resp.status_code)
    print("Headers:", resp.headers)
    print("Chunks:")
    for chunk in resp.iter_content(chunk_size=None):
        print(chunk)
except Exception as e:
    print("Error during request:", e)
