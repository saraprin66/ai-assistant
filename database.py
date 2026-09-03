import psycopg2
import json
import re
from sklearn.metrics.pairwise import cosine_similarity


class Database:

    def __init__(self):
        self.host = "localhost"
        self.database = "ai_assistant"
        self.user = "postgres"
        self.password = "123"

    def get_connection(self):
        return psycopg2.connect(
            host=self.host,
            database=self.database,
            user=self.user,
            password=self.password
        )

    def insert_chunk(
        self,
        document_id,
        document_name,
        chunk_index,
        content,
        embedding,
        source,
        metadata=None
    ):
        embedding_json = json.dumps(embedding)

        conn = self.get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO chunks
            (
                document_id,
                document_name,
                chunk_index,
                content,
                embedding,
                source,
                metadata
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                document_id,
                document_name,
                chunk_index,
                content,
                embedding_json,
                source,
                json.dumps(metadata or {})
            )
        )

        conn.commit()
        cur.close()
        conn.close()

    def search_similar(self, query_embedding, query_text, top_k=5):
        conn = self.get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT content, embedding, source, metadata
            FROM chunks;
            """
        )

        rows = cur.fetchall()

        query_words = set(
            re.findall(r'\b\w+\b', query_text.lower())
        )

        results = []

        important_phrases = [
            "débouchés",
            "conditions d'accès",
            "conditions et modalités d’accès",
            "passerelles",
            "prérequis",
            "validation",
            "stage",
            "pfe",
            "admission"
        ]

        query_lower = query_text.lower()

        for row in rows:
            content = row[0]
            doc_embedding = json.loads(row[1])
            source = row[2]
            metadata = row[3] or {}

            if len(doc_embedding) != len(query_embedding):
                continue

            semantic_score = cosine_similarity(
                [query_embedding],
                [doc_embedding]
            )[0][0]

            content_words = set(
                re.findall(r'\b\w+\b', content.lower())
            )

            common_words = query_words.intersection(content_words)

            keyword_score = (
                len(common_words) / len(query_words)
                if query_words
                else 0
            )

            content_lower = content.lower()

            phrase_score = 0

            for phrase in important_phrases:
                if phrase in query_lower and phrase in content_lower:
                    phrase_score += 0.3

            combined_score = (
                0.60 * semantic_score
                + 0.25 * keyword_score
                + 0.15 * min(phrase_score, 1.0)
            )

            results.append(
                (
                    content,
                    combined_score,
                    source,
                    metadata
                )
            )

        results.sort(
            key=lambda x: x[1],
            reverse=True
        )

        print("\n--- RETRIEVAL RESULTS ---")

        for result in results[:10]:
            print(
                f"Score: {result[1]:.4f} | "
                f"Source: {result[2]} | "
                f"Page: {result[3].get('page')} | "
                f"Content: {result[0][:200]}"
            )

        print("-------------------------\n")

        cur.close()
        conn.close()

        return results[:top_k]

    def delete_document_chunks(self, document_id):
        conn = self.get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            DELETE FROM chunks
            WHERE document_id = %s;
            """,
            (document_id,)
        )

        conn.commit()
        cur.close()
        conn.close()

    def dense_search(self, query_embedding, top_k=30):
        conn = self.get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT id, content, embedding, source, metadata
            FROM chunks;
            """
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()

        results = []
        for row in rows:
            doc_embedding = json.loads(row[2])
            if len(doc_embedding) != len(query_embedding):
                continue
            dense_score = cosine_similarity([query_embedding], [doc_embedding])[0][0]

            results.append((
                row[0],
                row[1],
                float(dense_score),
                row[3],
                row[4] or {}
            ))

        results.sort(
            key=lambda x: x[2],
            reverse=True
        )
        return results[:top_k]

    def sparse_search(self, query_text, top_k=30):
        if not query_text or not query_text.strip():
            return []

        conn = self.get_connection()
        cur = conn.cursor()

        # Extract alphanumeric words, codes (e.g. M111, M351, M115_2), acronyms
        terms = re.findall(r'[A-Za-zÀ-ÿ0-9_]+', query_text)

        stop_words = {
            "le", "la", "les", "un", "une", "des", "du", "de", "d", "l", "en", "et", "ou",
            "a", "au", "aux", "par", "pour", "dans", "sur", "avec", "sans", "sous",
            "qui", "que", "quoi", "dont", "où", "quel", "quelle", "quels", "quelles",
            "est", "sont", "ont", "avoir", "etre", "fait", "ce", "cette", "ces",
            "mon", "ton", "son", "notre", "votre", "leur", "the", "is", "at", "which"
        }

        filtered_terms = [t for t in terms if t.lower() not in stop_words and len(t) > 1]

        if filtered_terms:
            or_query = " | ".join(filtered_terms)
        else:
            or_query = " | ".join(terms) if terms else query_text

        sql = """
        SELECT
            id,
            content,
            ts_rank_cd(
                to_tsvector('simple', content),
                to_tsquery('simple', %s)
            ) AS sparse_score,
            source,
            metadata
        FROM chunks
        WHERE
            to_tsvector('simple', content) @@ to_tsquery('simple', %s)
            OR content ILIKE %s
        ORDER BY sparse_score DESC
        LIMIT %s;
        """

        first_kw = filtered_terms[0] if filtered_terms else query_text[:15]
        like_pattern = f"%{first_kw}%"

        try:
            cur.execute(sql, (or_query, or_query, like_pattern, top_k))
            rows = cur.fetchall()
        except Exception:
            conn.rollback()
            cur.execute(
                """
                SELECT id, content,
                       ts_rank(to_tsvector('simple', content), plainto_tsquery('simple', %s)) AS sparse_score,
                       source, metadata
                FROM chunks
                WHERE to_tsvector('simple', content) @@ plainto_tsquery('simple', %s)
                ORDER BY sparse_score DESC LIMIT %s;
                """,
                (query_text, query_text, top_k)
            )
            rows = cur.fetchall()

        results = []
        for row in rows:
            results.append((
                row[0],
                row[1],
                float(row[2]) if row[2] is not None else 0.0,
                row[3],
                row[4] or {}
            ))

        cur.close()
        conn.close()
        return results

    def reciprocal_rank_fusion(self, dense_results, sparse_results, top_k=30):
        k = 60
        rrf_scores = {}
        chunks = {}

        for rank, result in enumerate(dense_results, start=1):
            chunk_id = result[0]
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + (1.0 / (k + rank))
            chunks[chunk_id] = result

        for rank, result in enumerate(sparse_results, start=1):
            chunk_id = result[0]
            # Lexical boost for exact keyword matches (codes / names)
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + (1.2 / (k + rank))
            chunks[chunk_id] = result

        ranked = sorted(
            rrf_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        results = []
        for chunk_id, rrf_score in ranked[:top_k]:
            result = chunks[chunk_id]
            results.append((
                result[0],   # id
                result[1],   # content
                rrf_score,   # score
                result[3],   # source
                result[4]    # metadata
            ))

        return results