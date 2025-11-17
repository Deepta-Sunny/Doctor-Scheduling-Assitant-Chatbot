from agent.setup.llm_setup.llm_setup import setup_llm
from agent.utils.state.quickdoc_state import QuickDocState
from langchain_core.messages import HumanMessage, AIMessage
from agent.utils.tools.quickDoc_tool import quickDoc_tools
import os
from dotenv import load_dotenv

load_dotenv()

llm = setup_llm()

# Bind tools to the LLM
llm_with_tools = llm.bind_tools(quickDoc_tools)

# Specialty mapping: name -> ID (for reference, actual mapping is in the tool)
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
    """
    messages = state.get("messages", [])
    print("********routed to symptoms_node********")

    
    if not messages:
        return state
    
    user_text = messages[-1].content
    
    # Enhanced system prompt to guide the LLM
    system_prompt = f"""You are a medical assistant. When a user describes symptoms, you should:
1. Identify the most appropriate medical specialty from this list: {', '.join(SPECIALTY_MAP.keys())}
2. Use the get_doctor_details tool with the specialty name and city (if provided)
3. Always use EXACT specialty names from the list above

Examples:
- "I have chest pain in Mumbai" -> Call get_doctor_details with specialty_name="Cardiology", city="Mumbai"
- "Skin rash" -> Call get_doctor_details with specialty_name="Dermatology"
- "Headache and dizziness" -> Call get_doctor_details with specialty_name="Neurology"
"""
    
    # Prepend system prompt if not already there
    if not any(isinstance(msg, HumanMessage) and "medical assistant" in msg.content for msg in messages[:-1]):
        messages_with_context = [HumanMessage(content=system_prompt)] + messages
    else:
        messages_with_context = messages
    
    try:
        # Invoke LLM with tools to handle doctor search
        response = llm_with_tools.invoke(messages_with_context)
        print("**********symptomps response*****************",response)
        # If the LLM wants to use tools (search for doctors)
        if response.tool_calls:
            state["messages"].append(response)
            state["use_tools"] = True
        
        else:
            # Direct response without tools
            state["messages"].append(response)
            state["use_tools"] = False
            
    except Exception as e:
        error_msg = f"Error processing symptoms: {str(e)}"
        state["messages"].append(AIMessage(content=error_msg))
        state["use_tools"] = False
    
    return state
