import requests
import os

API_KEY = os.environ.get("GROK_API_KEY")

if not API_KEY:
    print("Error: GROK_API_KEY environment variable not set.")
    print("Run: set GROK_API_KEY=your_key_here")
    exit(1)

URL = "https://api.groq.com/openai/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

my_list = []

while True:
    user_input = input("You: ")
    my_list.append({"role": "user", "content": user_input})

    if user_input == "exit":
        break

    data = {
        "model": "llama-3.1-8b-instant",
        "messages": my_list
    }

    response = requests.post(URL, headers=headers, json=data)

    if response.status_code == 200:
        result = response.json()
        answer = result["choices"][0]["message"]["content"]
        my_list.append({"role": "assistant", "content": answer})
        print(f"\nGroq: {answer}\n")
    else:
        print(f"Error: {response.status_code} : {response.text}")
