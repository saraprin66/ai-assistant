import sys
sys.stdout.reconfigure(encoding='utf-8')
from database import Database
from embedder import Embedder
from reranker import Reranker
from llm_client import LLMClient
from rag_chatbot import RAGChatbot

db = Database()
emb = Embedder()
llm = LLMClient()
rerank = Reranker()
bot = RAGChatbot(db, emb, llm, rerank)

questions = [
    ("Q1", "Qui enseigne l'élément \"Systèmes d'exploitation\" (M115_2) dans la filière IL S1 ?"),
    ("Q2", "Quels sont les professeurs qui enseignent le module M351 \"Tendances et évolutions IT\" en IL S5 ?"),
    ("Q3", "Pouvez-vous résumer la liste des thématiques abordées dans la partie Algorithme du module M111 Algorithmes et Programmation (IL S1) ?"),
    ("Q4", "Quels sont les modules et éléments de cours enseignés par la professeure Pr. EL BICHRI Fadila sur l'ensemble de la filière Ingénierie Logicielle (IL) et quel est le total d'heures associé ?"),
    ("Q5", "Qui est le professeur responsable du module M111 Algorithmes et Programmation en Ingénierie Logicielle (IL) S1 et quel est le volume horaire alloué ?"),
    ("Q7", "Quels sont les crédits ECTS des modules du semestre IL S2 et quelles sont les dates de leurs épreuves de rattrapage respectives ?")
]

for label, q in questions:
    print(f"\n==================== {label} ====================")
    print("User Question:", q)
    rw = bot.rewrite_query(q, 100)
    print("Rewritten Query:", rw)
    
    
    sparse = db.sparse_search(rw, top_k=10)
    print(f"Top Sparse (total {len(sparse)}):")
    for s in sparse[:3]:
        print(f"  [id={s[0]} score={s[2]:.2f} doc={s[3]} p={s[4].get('page')} fil={s[4].get('filiere')} mod={s[4].get('module_code')}]")

    
    query_emb = emb.get_embedding(rw)
    dense = db.dense_search(query_emb, top_k=30)
    sparse_full = db.sparse_search(rw, top_k=30)
    fused = db.reciprocal_rank_fusion(dense, sparse_full, top_k=30)
    reranked = rerank.rerank(rw, fused, top_k=8)
    
    print("Reranked Top 8 Chunks:")
    for r in reranked:
        print(f"  [id={r[0]} doc={r[3]} p={r[4].get('page')} fil={r[4].get('filiere')} mod={r[4].get('module_code')}]")
        print(f"    Preview: {r[1][:120].replace(chr(10), ' ')}")
