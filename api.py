from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from reranker import Reranker

load_dotenv()

from database import Database
from embedder import Embedder
from llm_client import LLMClient
from rag_chatbot import RAGChatbot


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

database = Database()
embedder = Embedder()
llm_client = LLMClient()
reranker = Reranker()

chatbot = RAGChatbot(
    database,
    embedder,
    llm_client,
    reranker
)


class ChatRequest(BaseModel):
    question: str
    conversation_id: int


@app.get("/")
def home():
    return {
        "message": "ENSIASD Assistant API is running"
    }


@app.post("/chat")
def chat(request: ChatRequest):

    if not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )

    if request.conversation_id not in chatbot.conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    try:
        answer, sources = chatbot.ask(
            request.question,
            request.conversation_id
        )

        return {
            "answer": answer,
            "sources": sources
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chatbot error: {type(e).__name__}: {str(e)}"
        )


@app.post("/chat/stream")
def chat_stream(request: ChatRequest):

    if not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )

    if request.conversation_id not in chatbot.conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    try:
        return StreamingResponse(
            chatbot.ask_stream(
                request.question,
                request.conversation_id
            ),
            media_type="application/x-ndjson"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Streaming error: {type(e).__name__}: {str(e)}"
        )


@app.get("/history")
def history():
    return {
        "history": chatbot.conversation
    }


@app.get("/conversations/{id}")
def history_conversation(id: int):

    if id not in chatbot.conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    return {
        "conversation_id": id,
        "history": chatbot.conversation[id]
    }


@app.post("/conversations")
def create_conversation():
    conversation_id = chatbot.next_conversation_id

    chatbot.conversation[conversation_id] = []

    chatbot.next_conversation_id += 1

    return {
        "conversation_id": conversation_id
    }