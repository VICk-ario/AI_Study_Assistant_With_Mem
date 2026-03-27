from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import firebase_admin
import os

from firebase_admin import credentials, auth

from dotenv import load_dotenv

# Import your custom modules
from chatbot import get_tutor_response_web, handle_management_command
from database import get_or_create_user, init_db

load_dotenv()



# 1. Initialize Firebase (The Cached Way)

def init_firebase():
    try:
        # Check if already initialized by the library itself
        app = firebase_admin.get_app()
    except ValueError:
        # If not, initialize it
        cred = credentials.Certificate("firebase_key.json")
        app = firebase_admin.initialize_app(cred)
    return app

# Call the function at the top level
firebase_app = init_firebase()

init_db()  # Ensure the database is ready before handling any requests

app = FastAPI(title="Socratic Tutor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DATA MODELS ---
# We define exactly what a "Request" looks like
class ChatRequest(BaseModel):
    message: str
    user_id: str
    
# --- ENDPOINTS ---
@app.get("/")
def home():
    return {"status": "Socratic Brain is Online"}

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        # 1. First, check if the user is asking for a management task 
        # (e.g., "show my memory", "privacy policy", "export data")
        management_resp = await handle_management_command(request.message, request.user_id)
        
        if management_resp:
            return {"reply": management_resp}
            
        # 2. If it's not a command, run the full Socratic Brain pipeline
        # CRITICAL: We must 'await' this because it's an async function
        ai_response = await get_tutor_response_web(request.message, request.user_id)
        
        return {"reply": ai_response}

    except Exception as e:
        print(f"🔥 Backend Error: {e}")
        raise HTTPException(
            status_code=500, 
            detail="The Socratic Tutor hit a mental block. Check the server logs!"
        )
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)