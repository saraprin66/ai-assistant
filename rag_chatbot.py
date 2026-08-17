class RAGChatbot:

    def __init__(self, database, embedder, llm_client):
        self.database = database
        self.embedder = embedder
        self.llm_client = llm_client
        self.conversation = {}
        self.next_conversation_id = 1


    def rewrite_query(self, user_input, conversation_id):
        history = self.conversation.get(conversation_id, [])

        if not history:
            return user_input

        messages = [
            {
                "role":"system",
                "content":"""Rewrite the user's question into a standalone search query.

Use the conversation history only to understand what the user is referring to.

Do NOT answer the question.
Return ONLY the rewritten search query."""
            },
            {
                "role":"user",
                "content":f"""Conversation history:
            {history}

            Current question:
            {user_input}
            
Rewrite the current question into a standalone search query."""
            }
        ]
        return self.llm_client.generate(messages).strip()

    def ask(self, user_input, conversation_id):
        if conversation_id not in self.conversation:
            self.conversation[conversation_id] = []
        history = self.conversation[conversation_id]

        previous_context = " ".join(
            message["content"]
            for message in history[-2:]
        )

        search_query = f"{previous_context} {user_input}"

        query_embedding = self.embedder.get_embedding(search_query)

        search_results = self.database.search_similar(
            query_embedding,
            search_query
        )

        if not search_results:
            return "No similar documents found in the database.", []

        context = "\n\n".join(
            f"Source: {result[2]} - Page {result[3].get('page')}\n"
            f"Content: {result[0]}"
            for result in search_results
        )

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
5. If the user asks a follow-up question, use the conversation history only
to understand what the user is referring to. The actual answer must still
come from the CONTEXT.
6. Do not provide information that is not explicitly present in the CONTEXT."""
            }
        ]

        messages.append(
            {
                "role": "user",
                "content": f"""Context:
{context}

Question:
{user_input}"""
            }
        )

        answer = self.llm_client.generate(messages)

        sources = [
            f"{result[2]} - Page {result[3].get('page')}"
            for result in search_results
        ]

        self.conversation[conversation_id].append(
            {
                "role": "user",
                "content": user_input
            }
        )

        self.conversation[conversation_id].append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        return answer, sources

    def ask_stream(self, user_input, conversation_id):
        if conversation_id not in self.conversation:
            self.conversation[conversation_id] = []

        query_embedding = self.embedder.get_embedding(user_input)

        search_results = self.database.search_similar(
            query_embedding,
            user_input
        )

        if not search_results:
            yield "No similar documents found in the database."
            return

        context = "\n\n".join(
            f"Source: {result[2]} - Page {result[3].get('page')}\n"
            f"Content: {result[0]}"
            for result in search_results
        )

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
5. If the user asks a follow-up question, use the conversation history only
to understand what the user is referring to. The actual answer must still
come from the CONTEXT.
6. Do not provide information that is not explicitly present in the CONTEXT."""
            }
        ]

        messages.append(
            {
                "role": "user",
                "content": f"""Context:
{context}

Question:
{user_input}"""
            }
        )

        answer = ""

        for chunk in self.llm_client.generate_stream(messages):
            answer += chunk
            yield chunk

        self.conversation[conversation_id].append(
            {
                "role": "user",
                "content": user_input
            }
        )

        self.conversation[conversation_id].append(
            {
                "role": "assistant",
                "content": answer
            }
        )