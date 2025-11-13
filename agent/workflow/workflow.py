from agent.utils.nodes.clarify_node import clarify
from agent.utils.nodes.faq_node import faq
from agent.utils.nodes.router_node import intent_router
from agent.utils.nodes.symptoms_node import symptoms
from agent.utils.state.quickdoc_state import QuickDocState
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph,START,END

def create_workflow():
    """This is a function to create a compile the graph"""

    memory = MemorySaver
    workflow = StateGraph(QuickDocState)

    workflow.add_node("intent_router_node",intent_router)
    workflow.add_node("clarify_node",clarify)
    workflow.add_node("symptoms_node",symptoms)
    workflow.add_node("faq_node",faq)

    

    workflow.add_edge(START,"intent_router_node")
    workflow.add_conditional_edges(
        "intent_router_node",
        lambda state:state.get("next_node", "end"),
        {
            "clarify_node": "clarify_node",
            "symptoms_node": "symptoms_node",
            "faq_node": "faq_node",
            "end": END
        }
    )
    workflow.add_edge("clarify_node",END)
    workflow.add_edge("symptoms_node",END)
    workflow.add_edge("faq_node",END)

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
        print("Make sure you have 'pygraphviz' installed: pip install pygraphviz")


if __name__ == "__main__":
    visualize_graph()