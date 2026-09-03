from sentence_transformers import CrossEncoder
class Reranker:

    def __init__(self):
        self.model = CrossEncoder("BAAI/bge-reranker-v2-m3")

    def rerank(self, query, results, top_k=8):
        if not results:
            return []

        pairs = []

        for result in results:
            pairs.append([
                query,
                result[1]
            ])

        scores = self.model.predict(pairs)

        reranked = []

        for result, score in zip(results, scores):
            reranked.append((
                result[0],   #ID
                result[1],   # content
                float(score), # reranker score
                result[3],   # source
                result[4]    # metadata
            ))

        reranked.sort(
            key=lambda x: x[2],
            reverse=True
        )

        return reranked[:top_k]




 