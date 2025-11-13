from agent.setup.llm_setup.llm_setup import setup_llm
from agent.utils.state.quickdoc_state import QuickDocState
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
import os
from dotenv import load_dotenv

load_dotenv()

llm = setup_llm()

def clarify(state: QuickDocState) -> QuickDocState:
    """
    Ask for clarification when user message is unclear or ambiguous.
    Guides users to provide more specific information about their needs.
    """
    messages = state.get("messages", [])
    
    if not messages:
        # Initial greeting
        clarification = """Hello! I'm your medical scheduling assistant. I can help you with:

1. **Finding Doctors**: Tell me your symptoms or the type of doctor you need, and your location
2. **Answering Questions**: Ask about our services, hours, policies, or procedures

How can I assist you today?"""
        state["messages"].append(AIMessage(content=clarification))
        state["use_tools"] = False
        return state
    
    last_message = messages[-1].content
    
    # Create a prompt to generate helpful clarification
    system_prompt = f"""The user said: "{last_message}"

This message is unclear or too vague. Generate a helpful, friendly response that:
1. Acknowledges their message
2. Asks a specific clarifying question
3. Provides examples of what information would be helpful

Guide them towards either:
- Medical help: "I need a doctor for [symptom/condition] in [location]"
- General questions: "What are your office hours?" or "Do you accept insurance?"

Keep your response concise (2-3 sentences) and friendly."""
    
    try:
        response = llm.invoke([HumanMessage(content=system_prompt)])
        clarification = response.content
    except Exception as e:
        # Fallback clarification message
        clarification = """I'd be happy to help! Could you please provide more details? 

For medical appointments, please share:
- Your symptoms or the type of doctor you need (e.g., "I have a headache" or "I need a cardiologist")
- Your location or preferred area

For other questions, feel free to ask about our services, hours, or policies."""
    
    state["messages"].append(AIMessage(content=clarification))
    state["use_tools"] = False
    
    return state 