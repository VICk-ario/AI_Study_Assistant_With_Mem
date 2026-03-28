from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import firebase_admin
import os
from fastapi.responses import StreamingResponse
from chatbot import get_tutor_stream

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
        # Check for management commands first (they usually don't need streaming)
        management_resp = await handle_management_command(request.message, request.user_id)
        if management_resp:
            return {"reply": management_resp}

        # Return the stream
        gen = await get_tutor_stream(request.message, request.user_id)
        return StreamingResponse(gen, media_type="text/plain")

    except Exception as e:
        print(f"🔥 Backend Error: {e}")
        raise HTTPException(status_code=500, detail="The Brain hit a snag.")
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)