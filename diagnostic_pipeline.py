import sys
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


import json
import re
import sys
import os
from dotenv import load_dotenv

load_dotenv()

from database import Database
from embedder import Embedder
from reranker import Reranker


BENCHMARK_QUERIES = [
    {
        "category": "1. Exact names/codes",
        "query": "Qui est le professeur du module M115_2 ?",
        "keywords_expected": ["M115_2", "M115"],
        "description": "M115_2 teacher lookup",
    },
    {
        "category": "1. Exact names/codes",
        "query": "Quels sont les enseignants du module M351 ?",
        "keywords_expected": ["M351"],
        "description": "M351 teachers lookup",
    },
    {
        "category": "2. Content/topics",
        "query": "Quels sont les sujets abordés dans le module M111 ?",
        "keywords_expected": ["M111", "contenu", "programme", "algorith"],
        "description": "M111 Algorithm topics",
    },
    {
        "category": "3. Dates/numbers",
        "query": "Quels sont les modules enseignés par le professeur EL BICHRI et quel est le volume horaire total ?",
        "keywords_expected": ["EL BICHRI", "volume", "horaire"],
        "description": "Prof EL BICHRI modules + total hours",
    },
    {
        "category": "4. Multi-constraint",
        "query": "Quel est le professeur du module M111 et quel est le volume horaire ?",
        "keywords_expected": ["M111", "volume", "horaire", "professeur"],
        "description": "M111 professor + volume",
    },
    {
        "category": "5. Multi-document / multi-hop",
        "query": "Quelles sont les modalités d'évaluation du module M121 et quelle est la date d'examen ?",
        "keywords_expected": ["M121", "évaluation", "examen", "date"],
        "description": "M121 evaluation + exam date",
    },
    {
        "category": "5. Multi-document / multi-hop",
        "query": "Quels sont les crédits ECTS du semestre S2 de la filière IL et quelles sont les dates de rattrapage correspondantes ?",
        "keywords_expected": ["IL", "S2", "ECTS", "rattrapage"],
        "description": "IL S2 ECTS + rattrapage dates",
    },
]


def print_separator(char="=", width=90):
    print(char * width)


def print_header(text, char="=", width=90):
    print()
    print(char * width)
    print("  " + text)
    print(char * width)


def truncate(text, max_len=150):
    text = text.replace("\n", " ").replace("\r", "")
    if len(text) > max_len:
        return text[:max_len] + "..."
    return text


def search_db_for_keywords(db, keywords):
    
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, content, source, metadata FROM chunks;")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    matches = []
    for row in rows:
        chunk_id = row[0]
        content = row[1] or ""
        source = row[2] or ""
        metadata = row[3] or {}
        content_upper = content.upper()

        matched_kw = []
        for kw in keywords:
            if kw.upper() in content_upper:
                matched_kw.append(kw)

        if matched_kw:
            matches.append({
                "chunk_id": chunk_id,
                "source": source,
                "metadata": metadata,
                "matched_keywords": matched_kw,
                "keyword_count": len(matched_kw),
                "content_preview": truncate(content, 200)
            })

    
    matches.sort(key=lambda x: x["keyword_count"], reverse=True)
    return matches


def get_db_stats(db):
    
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM chunks;")
    total = cur.fetchone()[0]
    cur.execute("SELECT DISTINCT source FROM chunks;")
    sources = [r[0] for r in cur.fetchall()]
    cur.close()
    conn.close()
    return total, sources


def run_diagnostic(query_info, db, embedder, reranker_model):
   
    query = query_info["query"]
    keywords = query_info["keywords_expected"]

    print_header(f"CATEGORY: {query_info['category']}", char="=")
    print(f"  Query: {query}")
    print(f"  Description: {query_info['description']}")
    print(f"  Expected keywords: {keywords}")
    print()

    print("  +--- STAGE 0: DATABASE CONTENT SCAN ---")
    db_matches = search_db_for_keywords(db, keywords)
    if db_matches:
        
        full_matches = [m for m in db_matches if m["keyword_count"] == len(keywords)]
        partial_matches = [m for m in db_matches if m["keyword_count"] < len(keywords)]

        if full_matches:
            print(f"  | [OK] {len(full_matches)} chunk(s) contain ALL {len(keywords)} keywords")
            for i, m in enumerate(full_matches[:3]):
                print(f"  |   [{i+1}] id={m['chunk_id']} src={m['source']} kw={m['matched_keywords']}")
                print(f"  |       {m['content_preview'][:120]}")
        else:
            print(f"  | [WARN] NO chunk contains ALL keywords together")

        if partial_matches:
            print(f"  | [PARTIAL] {len(partial_matches)} chunk(s) with partial matches")
            for i, m in enumerate(partial_matches[:5]):
                print(f"  |   [{i+1}] id={m['chunk_id']} src={m['source']} matched={m['matched_keywords']}")
                print(f"  |       {m['content_preview'][:120]}")
    else:
        print(f"  | [FAIL] NO chunks found containing ANY of the keywords!")
    print("  +----------------------------------------")
    print()

   
    print("  +--- STAGE 1: SPARSE SEARCH (ts_rank, top 20) ---")
    sparse_results = db.sparse_search(query, top_k=20)
    if sparse_results:
        print(f"  | Returned {len(sparse_results)} results")
        for i, r in enumerate(sparse_results[:10]):
            chunk_id, content, score, source, meta = r
           
            found_kw = [kw for kw in keywords if kw.upper() in content.upper()]
            kw_tag = f" kw={found_kw}" if found_kw else ""
            print(f"  |   [{i+1}] id={chunk_id} score={score:.6f} src={source}{kw_tag}")
            print(f"  |       {truncate(content, 100)}")
    else:
        print(f"  | [FAIL] ZERO sparse results returned!")
    print("  +----------------------------------------")
    print()

    
    print("  +--- STAGE 2: DENSE SEARCH (cosine sim, top 20) ---")
    query_embedding = embedder.get_embedding(query)
    dense_results = db.dense_search(query_embedding, top_k=20)
    if dense_results:
        print(f"  | Returned {len(dense_results)} results")
        for i, r in enumerate(dense_results[:10]):
            chunk_id, content, score, source, meta = r
            found_kw = [kw for kw in keywords if kw.upper() in content.upper()]
            kw_tag = f" kw={found_kw}" if found_kw else ""
            print(f"  |   [{i+1}] id={chunk_id} score={score:.6f} src={source}{kw_tag}")
            print(f"  |       {truncate(content, 100)}")
    else:
        print(f"  | [FAIL] ZERO dense results returned!")
    print("  +----------------------------------------")
    print()

    
    print("  +--- STAGE 3: RRF FUSION (top 20) ---")
    rrf_results = db.reciprocal_rank_fusion(dense_results, sparse_results, top_k=20)
    if rrf_results:
        print(f"  | Returned {len(rrf_results)} results")
        for i, r in enumerate(rrf_results[:10]):
            chunk_id, content, rrf_score, source, meta = r
            found_kw = [kw for kw in keywords if kw.upper() in content.upper()]
            kw_tag = f" kw={found_kw}" if found_kw else ""
            print(f"  |   [{i+1}] id={chunk_id} rrf={rrf_score:.6f} src={source}{kw_tag}")
            print(f"  |       {truncate(content, 100)}")
    else:
        print(f"  | [FAIL] ZERO RRF results!")
    print("  +----------------------------------------")
    print()

    # ── Stage 4: BGE Reranker ──
    print("  +--- STAGE 4: BGE RERANKER (top 5) ---")
    reranked = reranker_model.rerank(query, rrf_results, top_k=5)
    if reranked:
        print(f"  | Returned {len(reranked)} results")
        for i, r in enumerate(reranked):
            chunk_id, content, rerank_score, source, meta = r
            found_kw = [kw for kw in keywords if kw.upper() in content.upper()]
            kw_tag = f" kw={found_kw}" if found_kw else ""
            print(f"  |   [{i+1}] id={chunk_id} rerank_score={rerank_score:.6f} src={source}{kw_tag}")
            print(f"  |       {truncate(content, 100)}")
    else:
        print(f"  | [FAIL] ZERO reranked results!")
    print("  +----------------------------------------")
    print()

    
    print("  +--- LOSS ANALYSIS ---")
    
    if db_matches:
        best_db = db_matches[0]
        best_id = best_db["chunk_id"]

        
        sparse_ids = [r[0] for r in sparse_results] if sparse_results else []
        dense_ids = [r[0] for r in dense_results] if dense_results else []
        rrf_ids = [r[0] for r in rrf_results] if rrf_results else []
        reranked_ids = [r[0] for r in reranked] if reranked else []

        in_sparse = best_id in sparse_ids
        in_dense = best_id in dense_ids
        in_rrf = best_id in rrf_ids
        in_reranked = best_id in reranked_ids

        sparse_rank = sparse_ids.index(best_id) + 1 if in_sparse else None
        dense_rank = dense_ids.index(best_id) + 1 if in_dense else None
        rrf_rank = rrf_ids.index(best_id) + 1 if in_rrf else None
        reranked_rank = reranked_ids.index(best_id) + 1 if in_reranked else None

        print(f"  | Best DB match: id={best_id} (matched {best_db['keyword_count']}/{len(keywords)} keywords)")
        print(f"  | Sparse:   {'[OK] rank ' + str(sparse_rank) if in_sparse else '[MISS] NOT FOUND'}")
        print(f"  | Dense:    {'[OK] rank ' + str(dense_rank) if in_dense else '[MISS] NOT FOUND'}")
        print(f"  | RRF:      {'[OK] rank ' + str(rrf_rank) if in_rrf else '[MISS] NOT FOUND'}")
        print(f"  | Reranked: {'[OK] rank ' + str(reranked_rank) if in_reranked else '[MISS] NOT FOUND'}")

        
        if not in_sparse and not in_dense:
            print(f"  | >>> FAILURE STAGE: RETRIEVAL (neither sparse nor dense found it)")
        elif in_sparse and not in_dense and not in_rrf:
            print(f"  | >>> FAILURE STAGE: RRF FUSION (sparse found it but it was lost in RRF)")
        elif not in_sparse and in_dense and not in_rrf:
            print(f"  | >>> FAILURE STAGE: RRF FUSION (dense found it but it was lost in RRF)")
        elif in_rrf and not in_reranked:
            print(f"  | >>> FAILURE STAGE: RERANKER (survived RRF but dropped by BGE reranker)")
        elif in_reranked:
            if reranked_rank <= 3:
                print(f"  | >>> CORRECT CHUNK SURVIVES to final context at rank {reranked_rank}")
            else:
                print(f"  | >>> Correct chunk survives but at low rank {reranked_rank}/5")
        
        
        if len(keywords) > 1:
            all_kw_chunks = {}
            for kw in keywords:
                kw_chunks = [m["chunk_id"] for m in db_matches if kw.upper() in [k.upper() for k in m["matched_keywords"]]]
                all_kw_chunks[kw] = kw_chunks
            
          
            all_ids = set()
            for ids in all_kw_chunks.values():
                all_ids.update(ids)
            
            if len(all_ids) > 1 and best_db["keyword_count"] < len(keywords):
                print(f"  | [WARN] FRAGMENTATION: keywords are split across {len(all_ids)} chunks")
                for kw, ids in all_kw_chunks.items():
                    print(f"  |     '{kw}' -> chunk(s) {ids[:5]}")
    else:
        print(f"  | >>> FAILURE STAGE: INGESTION/CHUNKING (content not found in DB at all)")
    print("  +----------------------------------------")

    return {
        "category": query_info["category"],
        "description": query_info["description"],
        "query": query,
        "db_matches": len(db_matches) if db_matches else 0,
        "db_full_matches": len([m for m in db_matches if m["keyword_count"] == len(keywords)]) if db_matches else 0,
        "sparse_count": len(sparse_results) if sparse_results else 0,
        "dense_count": len(dense_results) if dense_results else 0,
        "rrf_count": len(rrf_results) if rrf_results else 0,
        "reranked_count": len(reranked) if reranked else 0,
    }


def main():
    print_header("RAG PIPELINE DIAGNOSTIC TOOL", char="#")
    print()

    
    print("Loading models...")
    db = Database()
    embedder = Embedder()
    reranker_model = Reranker()
    print("Models loaded.\n")

    
    total_chunks, sources = get_db_stats(db)
    print(f"Database: {total_chunks} total chunks across {len(sources)} sources")
    for s in sorted(sources):
        print(f"  - {s}")
    print()

    
    summaries = []
    for q in BENCHMARK_QUERIES:
        result = run_diagnostic(q, db, embedder, reranker_model)
        summaries.append(result)

    
    print_header("SUMMARY TABLE", char="#")
    print(f"{'Category':<35} {'Description':<35} {'DB':<6} {'Sparse':<8} {'Dense':<8} {'RRF':<6} {'Rerank':<8}")
    print("-" * 110)
    for s in summaries:
        print(f"{s['category']:<35} {s['description']:<35} {s['db_matches']:<6} {s['sparse_count']:<8} {s['dense_count']:<8} {s['rrf_count']:<6} {s['reranked_count']:<8}")

    print("\n(DB = chunks containing any expected keyword, Sparse/Dense/RRF/Rerank = result counts)")
    print()


if __name__ == "__main__":
    main()
