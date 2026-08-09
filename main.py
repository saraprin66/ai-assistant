from dotenv import load_dotenv
load_dotenv()
import requests
import os
from db import search_similar
API_KEY =os.environ.get("GROK_API_KEY")

if not API_KEY:
    print("Error: GROK_API_KEY environment variable not set.")
    print("Run: set GROK_API_KEY=your_key_here")
    exit(1)


URL = f"https://api.groq.com/openai/v1/chat/completions"

my_list=[]


headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
while True:
    user_input=input("You:")

    if user_input == "exit":
        break

    my_list.append({"role": "user",
                    "content": user_input
                    })

    search_results = search_similar(user_input)

    if not search_results:
        print("No similar documents found in the database.")
        continue

    context="\n\n".join([result[0] for result in search_results])

    prompt= f"""
You are an ENSIASD assistant.

Answer the user's question using the provided context.
If the context does not contain enough information to answer,
say that you don't have enough information.

Context:
{context}

Question:
{user_input}
"""
    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [
          {
              "role":"user",
              "content": prompt
          }
      ]
    }

    print("Sending request to GROK API...")
    response = requests.post(URL,headers=headers,json=data)
    if response.status_code == 200:
        result = response.json()
        answer=result["choices"][0]["message"]["content"]
        my_list.append({"role": "assistant", "content": answer})

        print(f"\nGROK says: {answer}")
    else:
        print(f"Error: {response.status_code} : {response.text}")
