from langchain.tools import tool

@tool
def get_doctor_details():
    """gets the doctor details from the db"""
    return

quickDoc_tools = [get_doctor_details]
