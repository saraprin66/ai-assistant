from sentence_transformers import SentenceTransformer


class Embedder:

    def __init__(self):
        self.model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

    def get_embedding(self, text):
        embedding = self.model.encode(text)
        return embedding.tolist()