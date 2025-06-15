import requests

API_URL = "https://api-inference.huggingface.co/models/bigcode/starcoder"
headers = {"Authorization": "Bearer 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"}

def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)

    print("STATUS:", response.status_code)
    print("RESPONSE TEXT:", response.text)

    try:
        return response.json()
    except requests.exceptions.JSONDecodeError:
        return {"error": "Invalid JSON response"}

data = query({"inputs": "Quel est le président actuel de la France ?"})
print("DATA:", data)
