from langchain_core.tools import tool

@tool
def rag_tool(query: str) -> str:
    """Retrieve relevant information from a knowledge base based on the query."""
    # This is a placeholder for the actual RAG/vector store retrieval logic
    print(f"\n[RAG Tool] Retrieving information for query: {query}")
    return f"Simulated retrieved context for: {query}\n- Document 1: LangGraph allows building stateful, streaming multi-actor applications.\n- Document 2: RAG enhances model responses with specifically retrieved facts."
