from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

text = "I love pizza"
embedding = model.encode(text)

print("Text:", text)
print("Embedding length:", len(embedding))
print("First 5 numbers:", embedding[:5])
