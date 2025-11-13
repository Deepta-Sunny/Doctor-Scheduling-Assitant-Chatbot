from langchain.tools import tool
from agent.setup.chroma_db.pdf_processor import FAQProcessor

_faq_processor = None

def get_faq_processor():
    """Get or initialize the FAQ processor."""
    global _faq_processor
    if _faq_processor is None:
        _faq_processor = FAQProcessor()
    return _faq_processor

@tool
def search_faq(query: str, n_results: int = 3) -> str:
    """
    Search the FAQ knowledge base for relevant information.
    
    Args:
        query: The user's question or query
        n_results: Number of relevant results to return (default: 3)
        
    Returns:
        Relevant FAQ information as a formatted string
    """
    try:
        processor = get_faq_processor()
        results = processor.search_similar_documents(query, n_results)
        
        if not results or 'documents' not in results:
            return "No relevant FAQ information found."
        
        documents = results['documents'][0] 
        metadatas = results.get('metadatas', [[]])[0]
        
        formatted_results = []
        for i, (doc, metadata) in enumerate(zip(documents, metadatas), 1):
            filename = metadata.get('filename', 'Unknown')
            formatted_results.append(f"[Result {i} from {filename}]:\n{doc}\n")
        
        return "\n".join(formatted_results)
        
    except Exception as e:
        return f"Error searching FAQ: {str(e)}"

faq_tools = [search_faq]
