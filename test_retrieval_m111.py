import sys
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from database import Database
from embedder import Embedder
from llm_client import LLMClient
from reranker import Reranker
from rag_chatbot import RAGChatbot


question = (
    "Quel est le mode d'évaluation (pondération des contrôles continus et de "
    "l'examen final) du cours Structures de données avancée (M121) enseigné "
    "par Pr. KASRI Mohammed en IL S2, et à quelle date et heure est prévu "
    "son examen de rattrapage ?"
)

print("\n" + "=" * 80)
print("M111 RETRIEVAL DIAGNOSTIC")
print("=" * 80)
print(f"\nQUESTION:\n{question}\n")

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

search_query, results = chatbot.retrieve(
    question,
    conversation_id=1
)

print("=" * 80)
print("REWRITTEN SEARCH QUERY")
print("=" * 80)
print(search_query)

print("\n" + "=" * 80)
print(f"RERANKER TOP {len(results)} RESULTS")
print("=" * 80)

for i, result in enumerate(results, start=1):
    print(f"\n--- RESULT #{i} ---")
    print(f"Chunk ID : {result[0]}")
    print(f"RRF/Rerank score : {result[2]}")
    print(f"Source : {result[3]}")
    print(f"Page : {result[4].get('page')}")
    print(f"Metadata : {result[4]}")
    print("\nCONTENT:")
    print(result[1])

print("\n" + "=" * 80)
print("END")
print("=" * 80)