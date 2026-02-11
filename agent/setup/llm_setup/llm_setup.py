from langchain_openai import AzureChatOpenAI
import os
from dotenv import load_dotenv
load_dotenv()

def setup_llm():
    """Initialize and return the Azure Chat OpenAI LLM."""
        
    llm = AzureChatOpenAI(
        azure_endpoint=os.getenv("azure_endpoint").strip('"'),
        api_key=os.getenv("api_key").strip('"'),
        azure_deployment=os.getenv("azure_deployment").strip('"'),
        api_version=os.getenv("api_version").strip('"'),
    )
    
    return llm