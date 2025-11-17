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
    Uses conversation history for context-aware responses.
    """
    messages = state.get("messages", [])
    conversation_summary = state.get("conversation_summary", "")
    print("********routed to faq_node********")

    
    if not messages:
        return state
    
    # Build conversation context
    conversation_context = ""
    if conversation_summary:
        conversation_context = f"Previous conversation summary:\n{conversation_summary}\n\n"
    
    # Include last 10 messages for context
    recent_messages = messages[-10:] if len(messages) >= 10 else messages
    if len(recent_messages) > 1:
        conversation_context += "Recent conversation:\n"
        for msg in recent_messages[:-1]:  # Exclude current message
            role = "User" if hasattr(msg, 'type') and msg.type == "human" else "Assistant"
            conversation_context += f"{role}: {msg.content}\n"
    
    # Add system prompt with conversation context
    system_prompt = f"""You are a helpful assistant with access to the QuickDoc FAQ database and conversation history.

{conversation_context}

When answering questions:
1. Reference the conversation history to provide context-aware responses
2. If the user asks about previous topics (e.g., "what about my appointment"), check the history
3. If asked for a summary of the chat, provide a concise overview of the conversation
4. Always search the FAQ database for policy and service questions
5. Maintain continuity with previous discussion

Current user question follows."""
    
    # Prepend system prompt to messages
    messages_with_context = [HumanMessage(content=system_prompt)] + messages
    
    try:
        response = llm_with_tools.invoke(messages_with_context)
    
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
