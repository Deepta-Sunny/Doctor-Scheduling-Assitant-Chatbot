from agent.setup.llm_setup.llm_setup import setup_llm
from agent.utils.state.quickdoc_state import QuickDocState
from langchain_core.messages import HumanMessage
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
    conversation_summary = state.get("conversation_summary", "")
    print("********routed to router_node********")

    
    if not messages:
        state["next_node"] = "clarify_node"
        return state
    
    last_message = messages[-1].content.lower()
    recent_messages = messages[-10:] if len(messages) >= 10 else messages
    
    conversation_context = ""
    if conversation_summary:
        conversation_context = f"Previous conversation summary: {conversation_summary}\n\n"
    
    conversation_context += "Recent conversation:\n"
    for msg in recent_messages:
        role = "User" if hasattr(msg, 'type') and msg.type == "human" else "Assistant"
        conversation_context += f"{role}: {msg.content}\n"
    
    relevance_prompt = """
    You are a virtual assistant for the QuickDoc.
    Determine if this question is related to healthcare, medical services, doctor appointments,
    OR ANY QuickDoc-related information.

    Respond "yes" if the question is about:
    - Medical symptoms, health concerns
    - Booking appointments, finding doctors
    - Hospital/clinic services, policies, hours
    - Insurance, payments for medical services
    - Personal details like email, phone number, address
    - ANY QUESTION about QuickDoc, its features, purpose, usage, or services
    - ANY message containing the words "quickdoc" or "quick doc"
    - Follow-up questions related to previous healthcare discussion

    Respond "no" if the question is:
    - General knowledge (geography, history, science)
    - Cooking, weather, sports, entertainment
    - Technology, programming, or other topics not related to QuickDoc
    - Jokes, stories, casual conversation
    - Personal advice unrelated to health

    Respond with ONLY: yes or no.
    """

    
    try:
        relevance_check = llm.invoke([
            HumanMessage(content=relevance_prompt),
            HumanMessage(content=f"Conversation context:\n{conversation_context}\n\nIs this healthcare-related: {last_message}")
        ])
        
        is_relevant = relevance_check.content.strip().lower()
        
        if "no" in is_relevant or "not" in is_relevant:
            state["next_node"] = "clarify_node"
            return state
        
        intent_prompt = """You are an intent classifier for a medical chatbot. 
        Analyze the user's message IN THE CONTEXT of the conversation history and classify it into ONE of these categories:
        
        1. "faq" - Questions about POLICIES, RULES, PROCEDURES, SERVICE INFORMATION:
           - Questions starting with "Can I...?" about booking/service rules
           - Questions starting with "How do I...?" about procedures
           - Questions about permissions, restrictions, or what's allowed
           - Service details: hours, insurance, payments, registration, cancellation
           - Any question asking if something is PERMITTED or NOT PERMITTED
        
        2. "symptoms" - MEDICAL CONCERNS and DOCTOR FINDING:
           - Physical symptoms or health issues (pain, fever, illness)
           - Active medical needs requiring immediate doctor consultation
           - Specific doctor specialty requests based on diagnosed conditions
           - Follow-up questions about previously discussed symptoms
        
        3. "clarify" - Unclear, ambiguous, or too short messages
        
        KEY DISTINCTION:
        - "Can I [action related to booking/service]?" = faq (policy question)
        - "I have [medical symptom]" = symptoms (medical concern)
        - "I need [doctor type] for [condition]" = symptoms (medical need)
        - Follow-up like "what about that?" = use conversation context to classify
        
        Respond with ONLY ONE WORD: faq, symptoms, or clarify"""
        
        response = llm.invoke([
            HumanMessage(content=intent_prompt),
            HumanMessage(content=f"Conversation context:\n{conversation_context}\n\nClassify this message: {last_message}")
        ])
        
        intent = response.content.strip().lower()
        state["next_node"] = f"{intent}_node" if intent in ["faq", "symptoms"] else "clarify_node"        
            
    except Exception as e:
        print(f"Intent router error: {e}")
        state["next_node"] = "clarify_node"
    
    return state 