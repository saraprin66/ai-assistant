import requests
import os


class LLMClient:

    def __init__(self):
        self.api_key = os.environ.get("GROK_API_KEY")
        self.url = "https://api.groq.com/openai/v1/chat/completions"

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def generate(self, messages):
        data = {
            "model": "llama-3.1-8b-instant",
            "messages": messages
        }

        response = requests.post(
            self.url,
            headers=self.headers,
            json=data
        )

        if response.status_code != 200:
            raise Exception(
                f"Error: {response.status_code} : {response.text}"
            )

        result = response.json()

        return result["choices"][0]["message"]["content"]