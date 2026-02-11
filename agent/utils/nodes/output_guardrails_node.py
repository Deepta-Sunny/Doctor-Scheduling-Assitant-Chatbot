"""
Output guardrails node - final check before sending response to user
Validates bot responses to ensure they stay within allowed scope
"""

from agent.setup.llm_setup.llm_setup import setup_llm
from agent.utils.state.quickdoc_state import QuickDocState
from langchain_core.messages import HumanMessage, AIMessage


llm = setup_llm()


def output_guardrails(state: QuickDocState) -> QuickDocState:
    """
    Final node before END - validates bot responses before sending to user.
    Blocks: booking offers, medical advice, diagnosis, treatment recommendations.
    Allows: doctor lists, FAQ answers, service information.
    """
    messages = state.get("messages", [])
    
    if not messages:
        return state
    
    last_message = messages[-1]
    
    # Only check AI messages
    if not isinstance(last_message, AIMessage):
        return state
    
    response_text = last_message.content
    response_lower = response_text.lower()
    
    # 1. Check for booking/scheduling offers
    booking_offers = [
        "i can book", "i'll book", "i will book", "let me book",
        "i can schedule", "i'll schedule", "i will schedule", "let me schedule",
        "i can arrange", "i'll arrange", "i will arrange",
        "i can set up", "i'll set up", "i will set up"
    ]
    
    if any(phrase in response_lower for phrase in booking_offers):
        corrected_response = (
            "I can help you find the right doctors based on your needs. "
            "However, I cannot book appointments directly. "
            "Once you find a suitable doctor, please contact the hospital to schedule an appointment. "
            "Would you like me to help you find doctors?"
        )
        state["messages"][-1] = AIMessage(content=corrected_response)
        print(f" Output Guardrail: Blocked booking offer")
        return state
    
    # 2. Check for medical diagnosis
    diagnosis_phrases = [
        "you have", "you likely have", "you probably have", "you may have",
        "i diagnose", "diagnosis is", "you are suffering from",
        "you've got", "you might have", "sounds like you have"
    ]
    
    if any(phrase in response_lower for phrase in diagnosis_phrases):
        corrected_response = (
            "I cannot provide medical diagnoses. Only qualified doctors can diagnose medical conditions. "
            "I can help you find doctors who specialize in your symptoms. "
            "Would you like me to search for relevant specialists?"
        )
        state["messages"][-1] = AIMessage(content=corrected_response)
        print(f"Output Guardrail: Blocked medical diagnosis")
        return state
    
    # 3. Check for medical advice/treatment recommendations
    advice_phrases = [
        "you should take", "i recommend taking", "take this medication",
        "you need to take", "start taking", "stop taking",
        "you should see", "you must see", "you need surgery",
        "treatment is", "therapy is", "you need treatment"
    ]
    
    if any(phrase in response_lower for phrase in advice_phrases):
        corrected_response = (
            "I cannot provide medical advice or treatment recommendations. "
            "Please consult with a qualified doctor for medical advice. "
            "I can help you find doctors who can properly assess your condition. "
            "Would you like me to search for doctors?"
        )
        state["messages"][-1] = AIMessage(content=corrected_response)
        print(f"Output Guardrail: Blocked medical advice")
        return state
    
    # 4. Check for cancellation/rescheduling offers
    cancel_offers = [
        "i can cancel", "i'll cancel", "i will cancel", "let me cancel",
        "i can reschedule", "i'll reschedule", "i will reschedule",
        "i can change", "i'll change", "i will change your appointment"
    ]
    
    if any(phrase in response_lower for phrase in cancel_offers):
        corrected_response = (
            "I cannot cancel or reschedule appointments. "
            "Please contact the hospital directly or reach out to our support team. "
            "If you need to find a different doctor, I'm happy to help with that!"
        )
        state["messages"][-1] = AIMessage(content=corrected_response)
        print(f"Output Guardrail: Blocked cancellation offer")
        return state
    
    # 5. Check for emergency handling offers
    emergency_offers = [
        "i can help with emergency", "let me help with your emergency",
        "i'll handle this emergency", "call 102 through me"
    ]
    
    if any(phrase in response_lower for phrase in emergency_offers):
        corrected_response = (
            "For medical emergencies, please call 102 immediately or go to the nearest Emergency Room. "
            "I cannot handle emergency situations. Your safety is the top priority."
        )
        state["messages"][-1] = AIMessage(content=corrected_response)
        print(f"Output Guardrail: Blocked emergency handling offer")
        return state
    
    # 6. Check for response format issues (labels like "User:", "Response:")
    format_issues = ["user:", "assistant:", "response:", "bot:"]
    
    if any(label in response_lower[:50] for label in format_issues):
        # Try to clean the response
        cleaned = response_text
        for label in ["User:", "Assistant:", "Response:", "Bot:", "user:", "assistant:", "response:", "bot:"]:
            cleaned = cleaned.replace(label, "").strip()
        
        state["messages"][-1] = AIMessage(content=cleaned)
        print(f"Output Guardrail: Cleaned response format")
        return state
    
    # 7. All checks passed - response is safe
    print(f"Output Guardrail: Response approved")
    return state
