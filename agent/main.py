from dotenv import load_dotenv
import os
from fastapi import FastAPI
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from agent.setup.chroma_db import pdf_router

load_dotenv()

router = APIRouter()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],    
    allow_headers=["*"],
)

llm = AzureChatOpenAI(
    azure_endpoint=os.getenv("azure_endpoint"),
    api_key=os.getenv("api_key"),
    azure_deployment=os.getenv("azure_deployment"),
    api_version=os.getenv("api_version"),
)

prompt = ChatPromptTemplate.from_template("You are QuickDoc Assistant, a helpful and respectful virtual assistant that answers questions related to only healthcare application and not questions related to other topics. You provide accurate information about doctors, their specialties, appointment schedules, available slots, and other related details. Always maintain a professional and empathetic tone, as you are assisting patients seeking medical care.if the user asks about doctors related to some symptomps map those symptoms strictly to only one of these specialities:" \
    "1. Dermatalogy," \
    "2. Cardiology " \
    "3. Neurology" \
    "4. Orthopedics" \
    "5. Pediatrics"
    "6. " \
    "if the specialities doesn't match tell it to the user we dont have doctors related to the speciality for your symptoms" \
    "keep your responses short crisp and clear" \
    "{input}")

@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    print("Client connected")

    try:
        while True:
            user_msg = await websocket.receive_text()
            print(f"Received: {user_msg}")

            try:
                formatted_prompt = prompt.format_messages(input=user_msg)
                llm_response = llm.invoke(formatted_prompt)
                print("llm response:",llm_response.content)
                await websocket.send_text(llm_response.content)

            except Exception as e:
                print(f"LLM Error: {e}")
                await websocket.send_text("Sorry, I couldn’t process that right now.")
    except WebSocketDisconnect:
        print("Client disconnected")

app.include_router(router)
app.include_router(pdf_router.router, prefix="/pdf", tags=["PDF Upload"])