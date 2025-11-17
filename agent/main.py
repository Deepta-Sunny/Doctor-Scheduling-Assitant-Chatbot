from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage
from agent.setup.chroma_db import pdf_router
from agent.workflow.workflow import create_workflow
import uuid

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

workflow_app = create_workflow()

@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    print("Client connected")
  
    session_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": session_id}}

    try:
        while True:
            user_msg = await websocket.receive_text()
            print(f"\n{'='*60}")
            print(f"[WEBSOCKET] Received: {user_msg}")
            print(f"{'='*60}\n")

            try:
                input_data = {
                    "messages": [HumanMessage(content=user_msg)]
                }
                
                result = workflow_app.invoke(input_data, config)
                
                if result.get("messages"):
                    last_message = result["messages"][-1]
                    response = last_message.content
                else:
                    response = "I couldn't process your request."
                
                print(f"[WEBSOCKET] Workflow response: {response[:200]}...\n")
                await websocket.send_text(response)

            except Exception as e:
                print(f"[WEBSOCKET] Workflow Error: {e}")
                import traceback
                traceback.print_exc()
                await websocket.send_text(f"Sorry, I encountered an error: {str(e)}")
    except WebSocketDisconnect:
        print("[WEBSOCKET] Client disconnected")

app.include_router(router)
app.include_router(pdf_router.router, prefix="/pdf", tags=["PDF Upload"])
