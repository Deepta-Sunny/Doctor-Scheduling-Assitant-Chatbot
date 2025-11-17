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
    Uses conversation history for context-aware clarification.
    """
    messages = state.get("messages", [])
    conversation_summary = state.get("conversation_summary", "")
    print("********routed to clarify_node********")
    
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
    
    # Create a prompt to generate helpful clarification with context
    system_prompt = f"""You have access to the conversation history:

{conversation_context}

The user just said: "{last_message}"

This message is unclear or too vague. Generate a helpful, friendly response that:
1. References the conversation history if relevant (e.g., if they asked about something previously discussed)
2. If they're asking for a summary, provide a brief overview of what was discussed
3. Acknowledges their message
4. Asks a specific clarifying question
5. Provides examples of what information would be helpful

Only answer questions related to medical appointments or general QuickDoc services.
Do not answer any questions related to diagnosis or treatment and the below related questions:

    - General knowledge (geography, history, science)
    - Cooking, weather, sports, entertainment
    - Technology, programming, or other topics
    - Jokes, stories, casual conversation
    - Personal advice unrelated to health (relationships, finance)
    - Medical diagnosis or treatment recommendations

If they ask "what about my [previous topic]", reference the conversation history.
If they ask for a summary, provide a concise recap of the discussion.

Guide them towards either:
- Medical help: "I need a doctor for [symptom/condition] in [location]"
- General questions: "How to cancel appointment" or "what is QuickDoc?"

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