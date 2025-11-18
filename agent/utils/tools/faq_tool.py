from langchain.tools import tool
from agent.setup.chroma_db.pdf_processor import FAQProcessor
from agent.models.tool_inputs import FAQSearchInput
from pydantic import ValidationError

_faq_processor = None

def get_faq_processor():
    """Get or initialize the FAQ processor."""
    global _faq_processor
    if _faq_processor is None:
        _faq_processor = FAQProcessor()
    return _faq_processor

@tool
def search_faq(query: str, n_results: int = 5) -> str:
    """
    Search the FAQ knowledge base for relevant information about QuickDoc policies, procedures, and services.
    
    ALWAYS use this tool for ANY question about:
    - Booking appointments (for self or others)
    - Services and policies
    - Office hours, insurance, payments
    - Any "Can I...?" or "How do I...?" questions
    
    This tool uses semantic search to find similar questions, so it will match:
    - "Can I book for my sister?" matches "Can I book for someone else?"
    - "What are your hours?" matches "When are you open?"
    
    Args:
        query: The user's question (can be paraphrased, tool finds similar content)
        n_results: Number of relevant results to return (default: 5 for better coverage)
        
    Returns:
        Official FAQ information that MUST be used as the authoritative answer
    """
    try:
        validated_input = FAQSearchInput(query=query, n_results=n_results)
        query = validated_input.query 
        n_results = validated_input.n_results  
    except ValidationError as e:
        error_detail = e.errors()[0]
        if 'query' in str(error_detail.get('loc', '')):
            return "Please provide a more detailed question (at least 3 characters)."
        else:
            return "Invalid search parameters. Please try again."
    
    try:
        processor = get_faq_processor()
        results = processor.search_similar_documents(query, n_results)
        
        if not results or 'documents' not in results:
            return "No relevant FAQ information found in the database."
        
        documents = results['documents'][0] 
        metadatas = results.get('metadatas', [[]])[0]
        
        if not documents:
            return "No relevant FAQ information found in the database."
        
        formatted_results = ["=== OFFICIAL FAQ ANSWERS (Use these as the authoritative source) ===\n"]
        for i, (doc, metadata) in enumerate(zip(documents, metadatas), 1):
            filename = metadata.get('filename', 'Unknown')
            formatted_results.append(f"\n[FAQ Result {i} from {filename}]:\n{doc}\n")
        
        formatted_results.append("\n=== IMPORTANT: Base your response ONLY on the above FAQ information ===")
        
        return "\n".join(formatted_results)
        
    except Exception as e:
        return f"Error searching FAQ: {str(e)}"

faq_tools = [search_faq]
