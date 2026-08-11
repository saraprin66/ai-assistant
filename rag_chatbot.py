class RAGChatbot:

    def __init__(self, database, embedder, llm_client):
        self.database = database
        self.embedder = embedder
        self.llm_client = llm_client
        self.conversation = []

    def ask(self, user_input):

        if self.conversation:
            history = "\n".join(
                f"{message['role']}: {message['content']}"
                for message in self.conversation
            )

            rewrite_prompt = f"""
Rewrite the user's current question into a standalone question
that includes any necessary information from the conversation history.

Do not answer the question.
Return only the rewritten question.

Conversation history:
{history}

Current question:
{user_input}
"""

            rewrite_messages = [
                {
                    "role": "user",
                    "content": rewrite_prompt
                }
            ]

            rewritten_query = self.llm_client.generate(rewrite_messages)
        else:
            rewritten_query = user_input

        query_embedding = self.embedder.get_embedding(rewritten_query)

        search_results = self.database.search_similar(query_embedding)

        if not search_results:
            return "No similar documents found in the database."

        context = "\n\n".join(
            f"Source: {result[2]}\nContent: {result[0]}"
            for result in search_results)

        messages = [
            {
                "role": "system",
                "content": """You are an ENSIASD assistant.

You must answer ONLY from the CONTEXT provided in the user's message.

STRICT RULES:
1. Every factual statement in your answer must be supported by the CONTEXT.
2. Do not use your own knowledge.
3. Do not infer, assume, or complete missing information.
4. If the CONTEXT does not explicitly contain the answer, respond exactly:
"I don't have enough information to answer this question based on the available documents."
5. If the user asks a follow-up question, use the conversation history only to understand what the user is referring to. The actual answer must still come from the CONTEXT.
6. Do not provide information that is not explicitly present in the CONTEXT."""
            }
        ]

        

        messages.append({
            "role": "user",
            "content": f"""Context:
{context}

Question:
{user_input}"""
        })

        answer = self.llm_client.generate(messages)
        sources = [result[2] for result in search_results]

        self.conversation.append({
            "role": "user",
            "content": user_input
        })

        self.conversation.append({
            "role": "assistant",
            "content": answer
        })

        return answer, sources