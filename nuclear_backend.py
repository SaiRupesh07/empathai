from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from datetime import datetime
from typing import Optional
from fastapi.responses import JSONResponse

app = FastAPI()

# NUCLEAR CORS - ALLOWS EVERYTHING
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ALLOW ALL
    allow_credentials=True,
    allow_methods=["*"],  # ALLOW ALL METHODS
    allow_headers=["*"],  # ALLOW ALL HEADERS
    expose_headers=["*"],
)

# Add manual CORS headers middleware
@app.middleware("http")
async def add_cors_headers(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

class ChatRequest(BaseModel):
    user_id: str
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    user_id: str
    emotion_detected: str
    memories_used: int
    tone: str
    model_used: str
    session_id: Optional[str] = None
    timestamp: Optional[str] = None

# Storage
users_db = {}

@app.get("/")
async def root():
    return {"message": "EmpathAI Nuclear Backend", "status": "running", "cors": "ALLOW_ALL"}

@app.get("/health")
async def health():
    return JSONResponse(
        content={
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "cors": "enabled_for_all"
        },
        headers={"Access-Control-Allow-Origin": "*"}
    )

@app.get("/user/{user_id}")
async def get_user(user_id: str):
    return JSONResponse(
        content={
            "user_id": user_id,
            "exists": user_id in users_db,
            "total_conversations": users_db.get(user_id, {}).get("conversations", 0),
            "memory_count": 0,
            "last_active": datetime.now().isoformat()
        },
        headers={"Access-Control-Allow-Origin": "*"}
    )

@app.get("/user/{user_id}/memories")
async def get_memories(user_id: str):
    return JSONResponse(
        content={
            "user_id": user_id,
            "memories": [],
            "total_memories": 0
        },
        headers={"Access-Control-Allow-Origin": "*"}
    )

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        print(f"📨 Chat request: {request.user_id} - {request.message}")
        
        # Initialize user
        if request.user_id not in users_db:
            users_db[request.user_id] = {"conversations": 0}
        users_db[request.user_id]["conversations"] += 1
        
        # Simple response
        response_text = f"Hello {request.user_id}! You said: '{request.message}'. I'm your AI companion Alex!"
        
        response_data = {
            "response": response_text,
            "user_id": request.user_id,
            "emotion_detected": "joy",
            "memories_used": 0,
            "tone": "friendly",
            "model_used": "nuclear_backend",
            "session_id": request.session_id or f"session_{datetime.now().timestamp()}",
            "timestamp": datetime.now().isoformat()
        }
        
        return JSONResponse(
            content=response_data,
            headers={"Access-Control-Allow-Origin": "*"}
        )
        
    except Exception as e:
        return JSONResponse(
            content={
                "response": f"Error: {str(e)}",
                "user_id": request.user_id,
                "emotion_detected": "neutral",
                "memories_used": 0,
                "tone": "neutral",
                "model_used": "error",
                "session_id": "error",
                "timestamp": datetime.now().isoformat()
            },
            headers={"Access-Control-Allow-Origin": "*"}
        )

@app.options("/{path:path}")
async def options_handler(path: str):
    return JSONResponse(
        content={"message": "CORS allowed"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*"
        }
    )

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 EMPATHAI NUCLEAR BACKEND")
    print("=" * 60)
    print("✅ CORS: ALLOW EVERYTHING (*)")
    print("✅ Port: 8007")
    print("✅ Manual CORS headers on every response")
    print("✅ Guaranteed to work with frontend")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8007)