from agent.setup.llm_setup.llm_setup import setup_llm
from agent.utils.state.quickdoc_state import QuickDocState
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from agent.utils.tools.quickDoc_tool import quickDoc_tools
import os
from dotenv import load_dotenv

load_dotenv()

llm = setup_llm()

llm_with_tools = llm.bind_tools(quickDoc_tools)

def symptoms(state: QuickDocState) -> QuickDocState:
    """
    Handle symptom queries and doctor search.
    Uses quickDoc tools to search for doctors based on symptoms, specialty, location.
    Extracts symptoms, specialty, and location from user message.
    """
    messages = state.get("messages", [])
    
    if not messages:
        return state
    
    try:
        conversation_history = messages
        
        system_message = """You are a medical assistant helping users find doctors.

Your role:
1. Extract symptoms, medical specialty needed, and location from user messages
2. Use the search_doctors tool when you have enough information (specialty and location)
3. Ask clarifying questions if information is missing
4. Present doctor results in a friendly, organized way

Available information to extract:
- Symptoms: What the user is experiencing
- Specialty: What type of doctor they need (e.g., cardiologist, dermatologist, general physician)
- Location: City or area where they want to find a doctor

If the user mentions symptoms, try to suggest an appropriate specialty.
If information is incomplete, ask specific questions to gather what's needed.
When you have specialty and location, use the search_doctors tool."""

        messages_with_system = [HumanMessage(content=system_message)] + conversation_history
        
        response = llm_with_tools.invoke(messages_with_system)
        
        if response.tool_calls:
            state["messages"].append(response)
            state["use_tools"] = True
            state["next_node"] = "symptoms_node" 
            
            for tool_call in response.tool_calls:
                if tool_call.get("name") == "search_doctors":
                    args = tool_call.get("args", {})
                    if "symptoms" in args:
                        state["symptoms"] = args["symptoms"]
                    if "specialty" in args:
                        state["specialty"] = args["specialty"]
                    if "location" in args:
                        state["location"] = args["location"]
        else:
            state["messages"].append(response)
            state["use_tools"] = False
        
    except Exception as e:
        error_message = f"I apologize, but I encountered an error: {str(e)}. Please try describing your symptoms again."
        state["messages"].append(AIMessage(content=error_message))
        state["use_tools"] = False
    
    return state 