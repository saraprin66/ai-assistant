import psycopg2
import json
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer("all-MiniLM-L6-v2")


def load_documents():
    documents = [
        ("Python is a programming language.", "source1"),
        ("Java is a high-level programming language.", "source2"),
        ("JavaScript is used for web development.", "source3"),
        ("C++ is a general-purpose programming language.", "source4"),
        ("Ruby is a dynamic programming language.", "source5")
    ]
    return documents


def get_embedding(text):
    embedding = model.encode(text)
    return embedding.tolist()


def get_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="ai_assistant",
        user="postgres",
        password="123"
    )
    return conn


def insert_document(content, embedding, source):
    embedding_json = json.dumps(embedding)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO documents(content, embedding, source) VALUES (%s, %s, %s)",
        (content, embedding_json, source)
    )

    conn.commit()

    cur.close()
    conn.close()


def search_similar(query, top_k=3):
    embedding_query = get_embedding(query)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT content, embedding, source FROM documents;")

    rows = cur.fetchall()

    results = []

    for row in rows:
        content = row[0]
        doc_embedding = json.loads(row[1])
        source = row[2]

        if len(doc_embedding) != len(embedding_query):
            continue

        score = cosine_similarity(
            [embedding_query],
            [doc_embedding]
        )[0][0]

        results.append((content, score, source))

    results.sort(key=lambda x: x[1], reverse=True)

    cur.close()
    conn.close()

    return results[:top_k]


if __name__ == "__main__":
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM documents;")

    conn.commit()

    cur.close()
    conn.close()

    documents = load_documents()

    for content, source in documents:
        embedding = get_embedding(content)
        insert_document(content, embedding, source)

    search_results = search_similar("What is Java?")

    for result in search_results:
        print(f"Content: {result[0]}, Similarity Score: {result[1]}, Source: {result[2]}")