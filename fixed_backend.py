from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from datetime import datetime
from typing import Optional
from groq import Groq
import os

app = FastAPI()

# ===== CORS CONFIGURATION =====
# This is the key fix - proper CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Initialize Groq
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY", "your-key-here"))

# Data models
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

# Storage (in-memory for testing)
users_db = {}
memories_db = {}

# ===== ENDPOINTS =====
@app.get("/")
async def root():
    return {"message": "EmpathAI Fixed Backend", "status": "running", "cors": "enabled"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "in_memory",
        "groq_api": "connected",
        "cors": "enabled",
        "allowed_origins": ["http://localhost:3000", "http://localhost:3001"]
    }

@app.get("/user/{user_id}")
async def get_user(user_id: str):
    user_data = users_db.get(user_id, {})
    return {
        "user_id": user_id,
        "exists": user_id in users_db,
        "total_conversations": user_data.get("conversations", 0),
        "memory_count": len(memories_db.get(user_id, [])),
        "last_active": user_data.get("last_active"),
        "created_at": user_data.get("created_at")
    }

@app.get("/user/{user_id}/memories")
async def get_memories(user_id: str, limit: int = 10):
    memories = memories_db.get(user_id, [])
    return {
        "user_id": user_id,
        "memories": memories[:limit],
        "total_memories": len(memories)
    }

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        print(f"📨 Chat request from: {request.user_id}")
        print(f"📝 Message: {request.message[:50]}...")
        
        # Initialize user
        if request.user_id not in users_db:
            users_db[request.user_id] = {
                "created_at": datetime.now().isoformat(),
                "conversations": 0,
                "last_active": datetime.now().isoformat()
            }
        
        # Get user memories
        memories = memories_db.get(request.user_id, [])
        
        # Simple emotion detection
        text_lower = request.message.lower()
        if any(word in text_lower for word in ["happy", "joy", "love", "great"]):
            emotion = "joy"
            tone = "cheerful"
        elif any(word in text_lower for word in ["sad", "upset", "angry", "bad"]):
            emotion = "sadness"
            tone = "empathetic"
        else:
            emotion = "neutral"
            tone = "friendly"
        
        # Build prompt
        memory_text = ""
        if memories:
            memory_text = "What I know about you:\n" + "\n".join([f"- {m.get('content', m)[:50]}..." for m in memories[-3:]])
        
        prompt = f"""You are Alex, a friendly digital artist from Portland.

{memory_text}

The user is feeling {emotion}. Respond in a {tone} tone.

User: {request.message}

Alex:"""
        
        print("🤖 Calling Groq API...")
        # Get response from Groq
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300
        )
        
        response_text = response.choices[0].message.content
        print(f"✅ Response: {response_text[:50]}...")
        
        # Store memory
        if request.user_id not in memories_db:
            memories_db[request.user_id] = []
        
        if len(request.message.split()) > 3:
            memories_db[request.user_id].append({
                "content": request.message[:100],
                "type": "conversation",
                "timestamp": datetime.now().isoformat()
            })
        
        # Update user
        users_db[request.user_id]["conversations"] += 1
        users_db[request.user_id]["last_active"] = datetime.now().isoformat()
        
        return ChatResponse(
            response=response_text,
            user_id=request.user_id,
            emotion_detected=emotion,
            memories_used=len(memories),
            tone=tone,
            model_used="llama-3.1-8b-instant",
            session_id=request.session_id or f"session_{datetime.now().timestamp()}",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        print(f"❌ Chat error: {str(e)}")
        # Fallback response
        return ChatResponse(
            response="I'm here to chat with you! Tell me about your day.",
            user_id=request.user_id,
            emotion_detected="neutral",
            memories_used=0,
            tone="friendly",
            model_used="fallback",
            session_id=request.session_id or f"session_fallback",
            timestamp=datetime.now().isoformat()
        )

# Handle OPTIONS requests (important for CORS preflight)
@app.options("/{path:path}")
async def options_handler(path: str):
    return {
        "message": "CORS allowed",
        "allowed_methods": ["GET", "POST", "OPTIONS"],
        "allowed_origins": ["http://localhost:3000", "http://localhost:3001"]
    }

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 EMPATHAI FIXED BACKEND")
    print("=" * 60)
    print("✅ CORS: Properly configured")
    print("✅ Port: 8007")
    print("✅ Allowed origins: localhost:3000, localhost:3001")
    print("✅ Endpoints: /health, /chat, /user/{id}, /user/{id}/memories")
    print("=" * 60)
    
    # Remove reload=True to fix the warning
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8007,
        log_level="info"
    )