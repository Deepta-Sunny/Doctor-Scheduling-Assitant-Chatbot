from agent.setup.llm_setup.llm_setup import setup_llm
from agent.utils.state.quickdoc_state import QuickDocState
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
import os
from dotenv import load_dotenv

load_dotenv()

llm = setup_llm()

def intent_router(state: QuickDocState) -> QuickDocState:
    """
    Analyzes user intent and routes to appropriate node.
    Routes to:
    - faq_node: General questions, FAQ queries, information requests
    - symptoms_node: Medical symptoms, doctor search, appointment scheduling
    - clarify_node: Unclear or ambiguous messages
    """
    messages = state.get("messages", [])
    
    if not messages:
        state["next_node"] = "clarify_node"
        return state
    
    last_message = messages[-1].content.lower()
    
    # Intent classification prompt
    system_prompt = """You are an intent classifier for a medical chatbot. 
    Analyze the user's message and classify it into ONE of these categories:
    
    1. "faq" - General questions about services, hours, policies, procedures, insurance, or any non-medical information
    2. "symptoms" - Medical symptoms, finding doctors, booking appointments, health concerns
    3. "clarify" - Unclear, ambiguous, or too short messages that need clarification
    
    Examples:
    - "What are your office hours?" -> faq
    - "I have a headache" -> symptoms
    - "yes" -> clarify
    - "Do you accept my insurance?" -> faq
    - "I need a cardiologist" -> symptoms
    
    Respond with ONLY ONE WORD: faq, symptoms, or clarify"""
    
    try:
        response = llm.invoke([
            HumanMessage(content=system_prompt),
            HumanMessage(content=f"Classify this message: {last_message}")
        ])
        
        intent = response.content.strip().lower()
        
        if "faq" in intent:
            state["next_node"] = "faq_node"
        elif "symptom" in intent:
            state["next_node"] = "symptoms_node"
        elif "clarify" in intent:
            state["next_node"] = "clarify_node"
        else:
            state["next_node"] = "clarify_node"
            
    except Exception as e:
        print(f"Intent router error: {e}")
        state["next_node"] = "clarify_node"
    
    return state 