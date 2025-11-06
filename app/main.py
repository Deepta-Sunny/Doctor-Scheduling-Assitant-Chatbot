from dotenv import load_dotenv
import os
from fastapi import FastAPI
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

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

prompt = ChatPromptTemplate.from_template("You are QuickDoc Assistant. {input}")


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
                print(f"❌ LLM Error: {e}")
                await websocket.send_text("Sorry, I couldn’t process that right now.")
    except WebSocketDisconnect:
        print("❌ Client disconnected")


app.include_router(router)