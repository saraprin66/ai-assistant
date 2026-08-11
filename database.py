import psycopg2
import json
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

    def insert_document(self, content, embedding, source):
        embedding_json = json.dumps(embedding)

        conn = self.get_connection()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO documents(content, embedding, source) VALUES (%s, %s, %s)",
            (content, embedding_json, source)
        )

        conn.commit()

        cur.close()
        conn.close()

    def search_similar(self, query_embedding, top_k=3):
        threshold = 0.5

        conn = self.get_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT content, embedding, source FROM documents;"
        )

        rows = cur.fetchall()
        results = []

        for row in rows:
            content = row[0]
            doc_embedding = json.loads(row[1])
            source = row[2]

            if len(doc_embedding) != len(query_embedding):
                continue

            score = cosine_similarity(
                [query_embedding],
                [doc_embedding]
            )[0][0]

            if score >= threshold:
                results.append((content, score, source))
            else:
                print(
                    f"Document '{content}' skipped due to low similarity score: {score}"
                )

        results.sort(key=lambda x: x[1], reverse=True)

        cur.close()
        conn.close()

        return results[:top_k]