from dotenv import load_dotenv
from database import Database
from embedder import Embedder
from llm_client import LLMClient
from rag_chatbot import RAGChatbot

load_dotenv()

database = Database()
embedder = Embedder()
llm_client = LLMClient()

chatbot = RAGChatbot(
    database,
    embedder,
    llm_client
)

while True:
    user_input = input("You: ")

    if user_input == "exit":
        break

    answer, sources = chatbot.ask(user_input)

    print(f"\nGROK says: {answer}")
    print(f"\nSources: ")
    for source in sources :
        print(f"- {source}")