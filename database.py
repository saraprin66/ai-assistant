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

    def search_similar(self, query_embedding, query_text, top_k=3):

        conn = self.get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT content, embedding, source, metadata
            FROM chunks;
            """
        )

        rows = cur.fetchall()

        results = []

        query_words = set(
            re.findall(r'\b\w+\b', query_text.lower())
        )

        for row in rows:

            content = row[0]
            doc_embedding = json.loads(row[1])
            source = row[2]
            metadata = row[3]

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

            combined_score = (
                0.7 * semantic_score
                + 0.3 * keyword_score
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