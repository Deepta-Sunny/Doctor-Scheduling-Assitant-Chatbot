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
    print("********routed to router_node********")

    
    if not messages:
        state["next_node"] = "clarify_node"
        return state
    
    last_message = messages[-1].content.lower()
    
    # First check if the question is healthcare-related
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

    Respond "no" if the question is:
    - General knowledge (geography, history, science)
    - Cooking, weather, sports, entertainment
    - Technology, programming, or other topics not related to QuickDoc
    - Jokes, stories, casual conversation
    - Personal advice unrelated to health

    Respond with ONLY: yes or no.
    """

    
    try:
        # Check if question is healthcare-related
        relevance_check = llm.invoke([
            HumanMessage(content=relevance_prompt),
            HumanMessage(content=f"Is this healthcare-related: {last_message}")
        ])
        
        is_relevant = relevance_check.content.strip().lower()
        
        if "no" in is_relevant or "not" in is_relevant:
            # # Reject non-healthcare questions
            # rejection_message = "Sorry, we can't respond to questions that are not related to healthcare or diagnosis. I can only assist with medical concerns, doctor appointments, and our healthcare services."
            # state["messages"].append(AIMessage(content=rejection_message))
            state["next_node"] = "clarify_node"
            return state
        
        # If healthcare-related, classify intent
        intent_prompt = """You are an intent classifier for a medical chatbot. 
        Analyze the user's message and classify it into ONE of these categories:
        
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
        
        3. "clarify" - Unclear, ambiguous, or too short messages
        
        KEY DISTINCTION:
        - "Can I [action related to booking/service]?" = faq (policy question)
        - "I have [medical symptom]" = symptoms (medical concern)
        - "I need [doctor type] for [condition]" = symptoms (medical need)
        
        Respond with ONLY ONE WORD: faq, symptoms, or clarify"""
        
        response = llm.invoke([
            HumanMessage(content=intent_prompt),
            HumanMessage(content=f"Classify this message: {last_message}")
        ])
        
        intent = response.content.strip().lower()
        state["next_node"] = f"{intent}_node" if intent in ["faq", "symptoms"] else "clarify_node"        
            
    except Exception as e:
        print(f"Intent router error: {e}")
        state["next_node"] = "clarify_node"
    
    return state 