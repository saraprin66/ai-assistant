import requests
import os

API_KEY =os.environ.get("GROK_API_KEY")

if not API_KEY:
    print("Error: GROK_API_KEY environment variable not set.")
    print("Run: set GROK_API_KEY=your_key_here")
    exit(1)


URL = f"https://api.groq.com/openai/v1/chat/completions"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}
data = {
  "model": "llama-3.1-8b-instant",
  "messages": [
    {
      "role": "user",
      "content": "Hello, what are you? Answer in one sentence."
    }
  ]
}

print("Sending request to GROK API...")
response=requests.post(URL,headers=headers,json=data)

if response.status_code == 200:
    result = response.json()
    answer=result["choices"][0]["message"]["content"]
    print(f"\nGROK says: {answer}")
else:
    print(f"Error: {response.status_code} : {response.text}")