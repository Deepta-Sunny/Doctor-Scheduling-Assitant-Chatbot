from agent.setup.llm_setup.llm_setup import setup_llm
from agent.utils.state.quickdoc_state import QuickDocState
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from agent.utils.tools.faq_tool import faq_tools
import os
from dotenv import load_dotenv

load_dotenv()

llm = setup_llm()

llm_with_tools = llm.bind_tools(faq_tools)

def faq(state: QuickDocState) -> QuickDocState:
    """
    Handle FAQ queries - decides if tools are needed or generates direct response.
    """
    messages = state.get("messages", [])
    
    if not messages:
        return state
    
    try:
        response = llm_with_tools.invoke(messages)
    
        if response.tool_calls:
            state["messages"].append(response)
            state["use_tools"] = True
            state["next_node"] = "faq_node" 
        else:
            state["messages"].append(response)
            state["use_tools"] = False
        
    except Exception as e:
        error_message = f"I apologize, but I encountered an error: {str(e)}"
        state["messages"].append(AIMessage(content=error_message))
        state["use_tools"] = False
    
    return state
