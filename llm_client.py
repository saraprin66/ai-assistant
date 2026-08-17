import requests
import os
import json

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
            "model": "openai/gpt-oss-20b",
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

    def generate_stream(self, messages):
        data = {
            "model":"openai/gpt-oss-20b",
            "messages": messages,
            "stream": True
        }

        response = requests.post(
            self.url,
            headers=self.headers,
            json=data,
            stream=True
        )

        if response.status_code != 200:
            raise Exception(
                f"Error: {response.status_code} : {response.text}"
            )

        for line in response.iter_lines():
            if line:
                line = line.decode("utf-8")

                if line.startswith("data: "):
                    line = line[6:]
                    if line == "[DONE]":
                        break
                    data = json.loads(line)

                    content = data["choices"][0]["delta"].get("content")

                    if content :
                        yield content