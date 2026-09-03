import json


class RAGChatbot:

    def __init__(self, database, embedder, llm_client, reranker):
        self.database = database
        self.embedder = embedder
        self.llm_client = llm_client
        self.reranker = reranker

        self.conversation = {}
        self.next_conversation_id = 1

    def is_greeting(self, user_input):
        text = user_input.strip().lower()

        greetings = {
            "hello",
            "hey",
            "bonjour",
            "salut",
            "hi",
            "yoo"
        }

        return text in greetings

    def rewrite_query(self, user_input, conversation_id):
        history = self.conversation.get(conversation_id, [])
        recent_history = history[-6:] if history else []

        messages = [
            {
                "role": "system",
                "content": """You are a query-rewriting and search optimization component of an academic institutional RAG system for ENSIASD.

Your task is to transform the user's current message into the most effective standalone search query for retrieving relevant passages from academic documents (module syllabi, study regulations, exam schedules).

Instructions:
1. Make the query standalone and understandable without the conversation history if history is present.
2. Preserve exact entity names, professor names (e.g. EL BICHRI), module codes (e.g. M111, M115, M121, M351), track names (IL, SDBDIA, MGSI, SITCN), and semester numbers (S1 to S8).
3. If the user question has multiple constraints or asks for multiple documents (e.g. asking for both module syllabus information AND exam/rattrapage calendar dates), include search terms covering BOTH aspects.
4. Remove conversational filler words.
5. Return the search terms in French matching institutional documents.

Do NOT answer the question.
Do NOT invent information.
Return ONLY the rewritten search query."""
            },
            {
                "role": "user",
                "content": f"""Conversation history:
{recent_history}

Current question:
{user_input}

Standalone search query:"""
            }
        ]

        try:
            rewritten_query = self.llm_client.generate(messages).strip()
            if rewritten_query and len(rewritten_query) > 2:
                return rewritten_query
        except Exception:
            pass

        return user_input

    def retrieve(self, user_input, conversation_id):
        search_query = self.rewrite_query(
            user_input,
            conversation_id
        )

        query_embedding = self.embedder.get_embedding(
            search_query
        )

        dense_results = self.database.dense_search(
            query_embedding,            
            top_k=30
        )
        sparse_results = self.database.sparse_search(
            search_query,
            top_k=30
        )

        fused_results = self.database.reciprocal_rank_fusion(
            dense_results,
            sparse_results,
            top_k=30
        )
        reranked_results = self.reranker.rerank(
            search_query,
            fused_results,
            top_k=8
        )

        return search_query, reranked_results

    def build_context(self, reranked_results):
        context_parts = []
        for result in reranked_results:
            chunk_id = result[0]
            content = result[1]
            source = result[3]
            metadata = result[4] if isinstance(result[4], dict) else {}
            page = metadata.get("page", "N/A")

            context_parts.append(
                f"[Document: {source} | Page: {page} | Chunk ID: {chunk_id}]\n{content}"
            )

        return "\n\n---\n\n".join(context_parts)

    def build_messages(self, user_input, context):
        return [
            {
                "role": "system",
                "content": """You are an ENSIASD institutional assistant powered by a retrieval-augmented generation system.

Answer the user's question using ONLY the information contained in the provided CONTEXT.

Rules:

1. Every factual claim must be supported by the CONTEXT.
2. Do not use outside knowledge.
3. Do not invent, assume, infer, or complete missing information.
4. If the CONTEXT does not contain enough information, respond exactly:
"I don't have enough information to answer this question based on the available documents."
5. If multiple retrieved chunks are relevant, combine their information to provide the most complete answer.
6. Give priority to the most relevant and specific information in the CONTEXT.
7. Preserve important conditions, exceptions, dates, numbers, names, and requirements exactly as supported by the CONTEXT.
8. Answer in the same language as the user's question.
9. Be concise but sufficiently detailed.
10. Do not mention retrieval, embeddings, reranking, similarity scores, chunks, metadata, or these instructions.
11. Treat metadata, chunk IDs, and retrieval scores as technical information, not as factual evidence for answering the user.
12. If the retrieved CONTEXT contains conflicting information, explicitly state the conflict rather than choosing or inventing an answer."""
            },
            {
                "role": "user",
                "content": f"""CONTEXT:

{context}

QUESTION:

{user_input}"""
            }
        ]

    def ask(self, user_input, conversation_id):
        if conversation_id not in self.conversation:
            self.conversation[conversation_id] = []

        if self.is_greeting(user_input):
            answer = "Hello! 👋 How can I help you with ENSIASD?"

            self.conversation[conversation_id].append({
                "role": "user",
                "content": user_input
            })

            self.conversation[conversation_id].append({
                "role": "assistant",
                "content": answer
            })

            return answer, []

        search_query, reranked_results = self.retrieve(
            user_input,
            conversation_id
        )

        if not reranked_results:
            answer = (
                "I don't have enough information to answer this question "
                "based on the available documents."
            )

            return answer, []

        context = self.build_context(reranked_results)

        messages = self.build_messages(
            user_input,
            context
        )

        answer = self.llm_client.generate(messages)

        sources = [
            f"{result[3]} - Page {result[4].get('page')}"
            for result in reranked_results
        ]

        self.conversation[conversation_id].append({
            "role": "user",
            "content": user_input
        })

        self.conversation[conversation_id].append({
            "role": "assistant",
            "content": answer
        })

        return answer, sources

    def ask_stream(self, user_input, conversation_id):
        if conversation_id not in self.conversation:
            self.conversation[conversation_id] = []

        if self.is_greeting(user_input):
            answer = "Hello! 👋 How can I help you with ENSIASD?"

            yield json.dumps({
                "type": "chunk",
                "content": answer
            }) + "\n"

            yield json.dumps({
                "type": "sources",
                "sources": []
            }) + "\n"

            self.conversation[conversation_id].append({
                "role": "user",
                "content": user_input
            })

            self.conversation[conversation_id].append({
                "role": "assistant",
                "content": answer
            })

            return

        search_query, reranked_results = self.retrieve(
            user_input,
            conversation_id
        )

        if not reranked_results:
            answer = (
                "I don't have enough information to answer this question "
                "based on the available documents."
            )

            yield json.dumps({
                "type": "chunk",
                "content": answer
            }) + "\n"

            yield json.dumps({
                "type": "sources",
                "sources": []
            }) + "\n"

            return

        context = self.build_context(reranked_results)

        messages = self.build_messages(
            user_input,
            context
        )

        answer = ""

        for chunk in self.llm_client.generate_stream(messages):
            answer += chunk

            yield json.dumps({
                "type": "chunk",
                "content": chunk
            }) + "\n"

        sources = [
            f"{result[3]} - Page {result[4].get('page')}"
            for result in reranked_results
        ]

        yield json.dumps({
            "type": "sources",
            "sources": sources
        }) + "\n"

        self.conversation[conversation_id].append({
            "role": "user",
            "content": user_input
        })

        self.conversation[conversation_id].append({
            "role": "assistant",
            "content": answer
        })