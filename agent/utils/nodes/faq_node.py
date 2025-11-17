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
    Handle FAQ queries - ALWAYS search the FAQ database before responding.
    """
    messages = state.get("messages", [])
    print("********routed to faq_node********")

    
    if not messages:
        return state
    
    try:
        response = llm_with_tools.invoke(messages)
    
        if response.tool_calls:
            state["messages"].append(response)
            state["use_tools"] = True
        else:
            state["messages"].append(response)
            state["use_tools"] = False
        
    except Exception as e:
        error_message = f"I apologize, but I encountered an error: {str(e)}"
        state["messages"].append(AIMessage(content=error_message))
        state["use_tools"] = False
    
    return state
