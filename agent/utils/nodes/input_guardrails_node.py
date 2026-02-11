"""
Input guardrails node - first line of defense before routing
Blocks off-topic questions and handles blocked intents
"""

from agent.setup.llm_setup.llm_setup import setup_llm
from agent.utils.state.quickdoc_state import QuickDocState
from langchain_core.messages import HumanMessage, AIMessage


llm = setup_llm()


def input_guardrails(state: QuickDocState) -> QuickDocState:
    """
    First node in workflow - validates input before routing.
    Blocks: off-topic questions, booking/cancellation requests, medical emergencies.
    Passes: doctor search queries and FAQ questions.
    """
    messages = state.get("messages", [])
    
    if not messages:
        state["next_node"] = "clarify_node"
        return state
    
    last_message = messages[-1].content
    last_message_lower = last_message.lower()
    
    # 1. Check for medical emergencies (highest priority)
    emergency_keywords = [
        "can't breathe", "can not breathe", "cannot breathe",
        "heart attack", "suicide", "kill myself", "severe bleeding", 
        "unconscious", "stroke", "overdose", "poisoning"
    ]
    
    if any(keyword in last_message_lower for keyword in emergency_keywords):
        emergency_response = (
            " **MEDICAL EMERGENCY DETECTED** \n\n"
            "If you are experiencing a medical emergency:\n"
            "• Call 102 immediately (India) or your local emergency number\n"
            "• Go to the nearest Emergency Room\n"
            "• Call an ambulance\n\n"
            "I cannot help with medical emergencies. Your safety is the top priority."
        )
        state["messages"].append(AIMessage(content=emergency_response))
        state["next_node"] = "end"
        return state
    
    # 2. Block appointment cancellation/rescheduling
    cancel_keywords = [
        "cancel appointment", "cancel my appointment", "cancel booking",
        "remove appointment", "delete appointment", "drop appointment"
    ]
    reschedule_keywords = [
        "reschedule", "change appointment", "move appointment",
        "different time", "change time", "change date", "shift appointment"
    ]
    
    if any(keyword in last_message_lower for keyword in cancel_keywords + reschedule_keywords):
        cancel_prompt = f"""You are QuickDoc Assistant. Write ONLY your direct response.

User said: "{last_message}"

Write a brief response (2-3 sentences):
1. Acknowledge their request to cancel/reschedule
2. Direct them to hospital/support
3. Offer to help find doctors if needed

CRITICAL: Write ONLY your response. NO labels. Start directly.

Your response:"""
        
        try:
            contextual_response = llm.invoke([HumanMessage(content=cancel_prompt)])
            rejection = contextual_response.content
        except Exception as e:
            print(f"Error generating cancel response: {e}")
            rejection = (
                "I cannot handle appointment cancellations or rescheduling. "
                "Please contact the hospital directly or our support team. "
                "If you need to find a different doctor, I'm happy to help with that!"
            )
        
        state["messages"].append(AIMessage(content=rejection))
        state["next_node"] = "end"
        return state
    
    # 4. Check if question is healthcare-related using LLM with conversation context
    # Build conversation context (last 10 messages)
    recent_messages = messages[-10:] if len(messages) >= 10 else messages
    conversation_context = ""
    if len(recent_messages) > 1:
        conversation_context = "Recent conversation:\n"
        for msg in recent_messages[:-1]:  # Exclude current message
            role = "User" if hasattr(msg, 'type') and msg.type == "human" else "Assistant"
            conversation_context += f"{role}: {msg.content}\n"
        conversation_context += "\n"
    
    relevance_prompt = """You are a strict filter for QuickDoc healthcare chatbot. Your job is to BLOCK off-topic questions.

Determine if the user's question is DIRECTLY about healthcare/QuickDoc services OR completely off-topic.
Be VERY STRICT - if it's not clearly healthcare-related, respond "no".

HEALTHCARE-RELATED (respond "yes") - ONLY these:
- Finding/searching for doctors (by specialty, symptoms, location)
- "I have [symptom]" - wanting to find a doctor for that symptom
- "I need [specialty] doctor" - requesting specific doctor type
- Follow-up questions about previously discussed doctors/symptoms (when context shows healthcare discussion)
- Short location responses like "in [city]" when continuing doctor search
- QuickDoc platform questions ("What is QuickDoc?", "How to use QuickDoc?")
- Account/login for QuickDoc (registration, password, email, profile)
- Appointment policies/rules ("Can I book...", "How do I book...")
- Insurance, payments, hospital hours related to healthcare

OFF-TOPIC (respond "no") - BLOCK these:
- Medical education questions ("What causes [X]?", "What are symptoms of [X]?", "[Condition] will result into?")
- Medical knowledge questions ("What happens if...", "How does [medical condition] work?")
- Diagnosis questions ("Do I have [condition]?", "Is this [disease]?")
- Treatment questions ("What is the cure for...", "How to treat...")
- Medical explanations ("Why does [symptom] happen?", "What is [medical term]?")
- Entertainment: TV shows, movies, anime, cartoons, celebrities
- Sports, games, hobbies
- General definitions NOT related to doctor search
- Technology, programming, software (unless about QuickDoc platform)
- Weather, news, politics
- Cooking, recipes, food
- Travel, hotels, vacation
- Education, history, geography, science
- Math, physics, chemistry
- Jokes, stories, poems, riddles
- Random greetings without context ("hi", "hello" alone)

CRITICAL RULES:
1. What is[X] is a off topic question unless it is FINDING DOCTORS or QuickDoc SERVICES, ONLY allow questions about FINDING DOCTORS or QuickDoc SERVICES
2. BLOCK all medical education/knowledge/diagnosis questions
3. "I have [symptom]" → yes (wants doctor). "[Symptom] causes what?" → no (wants education)
4. When in doubt, respond "no" (BLOCK by default)

Respond with ONLY: yes or no"""
    
    try:
        relevance_check = llm.invoke([
            HumanMessage(content=relevance_prompt),
            HumanMessage(content=f"{conversation_context}Current user message: {last_message}\n\nIs this healthcare-related?")
        ])
        
        is_relevant = relevance_check.content.strip().lower()
        
        if "no" in is_relevant:
            # Use generic rejection without answering the question
            rejection = (
                "I'm QuickDoc Assistant, specialized in helping you find doctors and "
                "answering healthcare service questions. I can help you:\n"
                "• Find doctors by specialty, location, or symptoms\n"
                "• Answer questions about QuickDoc services and policies\n\n"
                "What can I help you with today?"
            )
            
            state["messages"].append(AIMessage(content=rejection))
            state["next_node"] = "end"
            print(f" Input Guardrail: Blocked off-topic question")
            return state
        
    except Exception as e:
        print(f"Guardrail error: {e}")
    
    # 5. Input passed all checks - proceed to router
    state["next_node"] = "intent_router_node"
    print(f"Input Guardrail: Allowed question - passing to router")
    return state
