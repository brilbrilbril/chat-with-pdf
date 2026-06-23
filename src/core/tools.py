SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "search_documents",
        "description": (
            "Search the indexed document knowledge base for information relevant to a query. "
            "Returns text chunks with their source (file name, page/slide/sheet). "
            "Always call this before answering questions about document content."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query — rephrase the user question as a concise information need.",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of chunks to retrieve (default 10, max 15).",
                    "default": 10,
                },
            },
            "required": ["query"],
        },
    },
}