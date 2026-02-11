from agent.utils.nodes.tool_node import tools_node
from agent.utils.nodes.clarify_node import clarify
from agent.utils.nodes.faq_node import faq
from agent.utils.nodes.router_node import intent_router
from agent.utils.nodes.symptoms_node import symptoms
from agent.utils.nodes.input_guardrails_node import input_guardrails
from agent.utils.nodes.output_guardrails_node import output_guardrails
from agent.utils.state.quickdoc_state import QuickDocState
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph,START,END

def create_workflow():
    """
    Create and compile the LangGraph workflow with guardrails.
    Flow: Input Guardrails -> Router -> Handler -> Output Guardrails -> End
    """

    memory = MemorySaver()
    workflow = StateGraph(QuickDocState)

    # Add all nodes with input and output guardrails
    workflow.add_node("input_guardrails_node", input_guardrails)
    workflow.add_node("intent_router_node", intent_router)
    workflow.add_node("clarify_node", clarify)
    workflow.add_node("symptoms_node", symptoms)
    workflow.add_node("faq_node", faq)
    workflow.add_node("tools_node", tools_node)
    workflow.add_node("output_guardrails_node", output_guardrails)

    # Start with input guardrails (first line of defense)
    workflow.add_edge(START, "input_guardrails_node")
    
    # From input guardrails: either block (end) or pass to router
    workflow.add_conditional_edges(
        "input_guardrails_node",
        lambda state: state.get("next_node", "intent_router_node"),
        {
            "intent_router_node": "intent_router_node",
            "end": END
        }
    )
    # Route from intent router to appropriate handler
    workflow.add_conditional_edges(
        "intent_router_node",
        lambda state: state.get("next_node", "clarify_node"),
        {
            "clarify_node": "clarify_node",
            "symptoms_node": "symptoms_node",
            "faq_node": "faq_node"
        }
    )
    workflow.add_conditional_edges(
        "symptoms_node",
        lambda state: state.get("use_tools", False),
        {
            True: "tools_node",
            False: "output_guardrails_node"
        }
    )
    workflow.add_conditional_edges(
        "faq_node",
        lambda state: state.get("use_tools", False),
        {
            True: "tools_node",
            False: "output_guardrails_node"
        }
    )
    workflow.add_conditional_edges(
        "tools_node",
        lambda state: state.get("calling_node", "symptoms_node"),
        {
            "symptoms_node": "symptoms_node",
            "faq_node": "faq_node"
        }
    )
    
    # Clarify node asks for more info, then user responds and goes back to router
    workflow.add_edge("clarify_node", "intent_router_node")
    
    # Output guardrails is the final node before user
    workflow.add_edge("output_guardrails_node", END)

    agent = workflow.compile(checkpointer=memory)

    return agent


def invoke_workflow(input_data):
    """Invoke the workflow with input data"""
    agent  = create_workflow()
    result = agent.invoke(input_data)
    return result


def visualize_graph():
    """Generate and save the workflow graph as PNG"""
    agent = create_workflow()
    
    try:
        png_data = agent.get_graph().draw_mermaid_png()
        
        with open("workflow_graph.png", "wb") as file:
            file.write(png_data)
        
        print("Graph visualization saved as 'workflow_graph.png'")
    except Exception as exception:
        print(f"Error generating graph visualization: {exception}")
        
if __name__ == "__main__":
    visualize_graph()