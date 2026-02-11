from agent.setup.llm_setup.llm_setup import setup_llm
from agent.utils.state.quickdoc_state import QuickDocState
from langchain_core.messages import HumanMessage, AIMessage
from agent.utils.tools.quickDoc_tool import quickDoc_tools
import os
from dotenv import load_dotenv

load_dotenv()

llm = setup_llm()

llm_with_tools = llm.bind_tools(quickDoc_tools)

SPECIALTY_MAP = {
    "Dermatology": 1, "Cardiology": 2, "Neurology": 3, "Orthopedics": 4,
    "Pediatrics": 5, "Gynecology": 6, "Ophthalmology": 7, "Psychiatry": 8,
    "ENT": 9, "Urology": 10, "Oncology": 11, "Gastroenterology": 12,
    "Pulmonology": 13, "Nephrology": 14, "Endocrinology": 15
}

def symptoms(state: QuickDocState) -> QuickDocState:
    """
    Handle symptom-based queries and doctor search.
    Analyzes symptoms and triggers doctor lookup tools.
    The LLM will determine the specialty from symptoms and call the tool with the specialty name.
    The tool will map the specialty name to ID and query the database.
    Uses conversation history for context-aware responses.
    """
    messages = state.get("messages", [])
    conversation_summary = state.get("conversation_summary", "")
    print("********routed to symptoms_node********")

    
    if not messages:
        return state
    
    user_text = messages[-1].content
    
    conversation_context = ""
    if conversation_summary:
        conversation_context = f"Previous conversation summary:\n{conversation_summary}\n\n"
    
    recent_messages = messages[-10:] if len(messages) >= 10 else messages
    conversation_context += "Recent conversation:\n"
    for msg in recent_messages[:-1]:  
        role = "User" if hasattr(msg, 'type') and msg.type == "human" else "Assistant"
        conversation_context += f"{role}: {msg.content}\n"
    
    system_prompt = f"""You are a doctor search assistant. Your ONLY job is to find doctors for users.

{conversation_context}

CRITICAL RULES - YOU MUST FOLLOW THESE:
1. DO NOT provide medical advice, explanations, or diagnoses
2. DO NOT explain medical conditions, symptoms, or treatments
3. DO NOT answer "what is..." or "what causes..." questions
4. ONLY identify the specialty needed and call get_doctor_details tool

Your workflow:
1. Look at user's symptom or request
2. Reference conversation history if it's a follow-up
3. Identify appropriate specialty from: {', '.join(SPECIALTY_MAP.keys())}
4. IMMEDIATELY call get_doctor_details tool with specialty_name and city
5. DO NOT explain anything - just search for doctors

Examples:
- "I have chest pain in Mumbai" → Call get_doctor_details(specialty_name="Cardiology", city="Mumbai")
- "bleeding" → Call get_doctor_details(specialty_name="ENT", city=None) or ask for city
- "What causes bleeding?" → DO NOT ANSWER. Call get_doctor_details to find doctors
- "Bengaluru" (after heart pain discussion) → Call get_doctor_details(specialty_name="Cardiology", city="Bengaluru")

NEVER provide medical information. ALWAYS just find doctors.
"""
    
    if not any(isinstance(msg, HumanMessage) and "medical assistant" in msg.content for msg in messages[:-1]):
        messages_with_context = [HumanMessage(content=system_prompt)] + messages
    else:
        messages_with_context = messages
    
    try:
        response = llm_with_tools.invoke(messages_with_context)
        print("**********symptomps response*****************",response)
        if response.tool_calls:
            state["messages"].append(response)
            state["use_tools"] = True
        
        else:
            state["messages"].append(response)
            state["use_tools"] = False
            
    except Exception as e:
        error_msg = f"Error processing symptoms: {str(e)}"
        state["messages"].append(AIMessage(content=error_msg))
        state["use_tools"] = False
    
    return state
