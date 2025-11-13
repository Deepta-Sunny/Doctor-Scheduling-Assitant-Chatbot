from langgraph.prebuilt import ToolNode
from agent.utils.tools.quickDoc_tool import quickDoc_tools
from agent.utils.tools.faq_tool import faq_tools

all_tools = quickDoc_tools + faq_tools

tools_node = ToolNode(all_tools)