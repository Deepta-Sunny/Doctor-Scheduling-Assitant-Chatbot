from typing import Annotated, Optional, List
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages, BaseMessage

class QuickDocState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    symptoms: Optional[str]
    specialty: Optional[str]
    location: Optional[str]
    doctor_results: Optional[str]  
    next_node: Optional[str]
    use_tools: Optional[bool]
