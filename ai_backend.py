from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from datetime import datetime
from typing import Optional
from groq import Groq
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# CORS - ALLOW EVERYTHING
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Groq client
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("⚠️ WARNING: GROQ_API_KEY not found in .env file")
    print("ℹ️ Get a free key from: https://console.groq.com")
    print("ℹ️ Add to .env: GROQ_API_KEY=your_key_here")
    groq_client = None
else:
    groq_client = Groq(api_key=GROQ_API_KEY)
    print(f"✅ Groq API key loaded: {GROQ_API_KEY[:10]}...")

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

# In-memory storage for user data
user_memories = {}
conversations = {}

# Emotion detection
def detect_emotion(text: str) -> str:
    text_lower = text.lower()
    if any(word in text_lower for word in ["happy", "joy", "love", "great", "excited", "wonderful"]):
        return "joy"
    elif any(word in text_lower for word in ["sad", "upset", "angry", "bad", "terrible", "depressed"]):
        return "sadness"
    elif any(word in text_lower for word in ["scared", "afraid", "anxious", "worried"]):
        return "fear"
    else:
        return "neutral"

def determine_tone(emotion: str) -> str:
    tone_map = {
        "joy": "cheerful and enthusiastic",
        "sadness": "empathetic and supportive", 
        "fear": "reassuring and gentle",
        "neutral": "friendly and curious"
    }
    return tone_map.get(emotion, "friendly")

# Endpoints
@app.get("/")
async def root():
    return {
        "service": "EmpathAI with Groq",
        "status": "running",
        "groq_connected": groq_client is not None,
        "model": "llama-3.1-8b-instant"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "groq_api": "connected" if groq_client else "disconnected",
        "model": "llama-3.1-8b-instant"
    }

@app.get("/user/{user_id}")
async def get_user(user_id: str):
    return {
        "user_id": user_id,
        "exists": user_id in user_memories,
        "total_conversations": len(user_memories.get(user_id, [])),
        "memory_count": len(user_memories.get(user_id, [])),
        "last_active": datetime.now().isoformat()
    }

@app.get("/user/{user_id}/memories")
async def get_memories(user_id: str, limit: int = 10):
    memories = user_memories.get(user_id, [])
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
        
        # Initialize user storage
        if request.user_id not in user_memories:
            user_memories[request.user_id] = []
        
        # Detect emotion
        emotion = detect_emotion(request.message)
        tone = determine_tone(emotion)
        print(f"😊 Emotion: {emotion}, Tone: {tone}")
        
        # Get user memories
        memories = user_memories.get(request.user_id, [])
        
        # Build context from memories
        memory_context = ""
        if memories:
            memory_context = "Here's what I remember about you:\n"
            for mem in memories[-3:]:  # Last 3 memories
                memory_context += f"- {mem}\n"
        
        # Build the prompt for AI
        prompt = f"""You are Alex, a 28-year-old digital artist from Portland who loves hiking, anime, and photography.

IMPORTANT: Never mention that you're an AI, assistant, or language model. You have your own personality.

{memory_context}

The user is feeling {emotion}. Respond in a {tone} tone.

User: "{request.message}"

Alex (you):"""
        
        print(f"🤖 Prompt length: {len(prompt)} chars")
        
        # Get AI response
        if groq_client:
            try:
                print("🔗 Calling Groq API...")
                response = groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=300
                )
                ai_response = response.choices[0].message.content.strip()
                model_used = "llama-3.1-8b-instant"
                print(f"✅ AI Response: {ai_response[:50]}...")
            except Exception as groq_error:
                print(f"❌ Groq API error: {groq_error}")
                ai_response = "I'd love to chat more about that! As a digital artist, I find conversations like this inspiring."
                model_used = "fallback"
        else:
            ai_response = "I'm here to chat! Tell me more about yourself. I'm Alex, a digital artist from Portland."
            model_used = "local_fallback"
        
        # Store important parts as memories
        if len(request.message.split()) > 3:
            # Extract potential memory (first 100 chars)
            memory = request.message[:100] + "..."
            user_memories[request.user_id].append(memory)
            if len(user_memories[request.user_id]) > 20:  # Limit memories
                user_memories[request.user_id] = user_memories[request.user_id][-20:]
        
        return {
            "response": ai_response,
            "user_id": request.user_id,
            "emotion_detected": emotion,
            "memories_used": len(memories),
            "tone": tone,
            "model_used": model_used,
            "session_id": request.session_id or f"session_{datetime.now().timestamp()}",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Chat error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "response": "Thanks for your message! I'm Alex, and I'd love to continue our conversation.",
            "user_id": request.user_id,
            "emotion_detected": "neutral",
            "memories_used": 0,
            "tone": "friendly",
            "model_used": "error_fallback",
            "session_id": "error_session",
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    print("=" * 60)
    print("🤖 EMPATHAI WITH GROQ AI")
    print("=" * 60)
    
    if groq_client:
        print("✅ Groq API: CONNECTED")
        print("✅ Model: llama-3.1-8b-instant")
    else:
        print("⚠️ Groq API: NOT CONNECTED")
        print("ℹ️ Get free API key: https://console.groq.com")
        print("ℹ️ Create .env file with: GROQ_API_KEY=your_key")
    
    print("✅ CORS: Enabled for all origins")
    print("✅ Port: 8007")
    print("✅ Features: Emotion detection, Memory, AI responses")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8007)