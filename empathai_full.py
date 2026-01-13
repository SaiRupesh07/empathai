import os
import json
import logging
from datetime import datetime
from typing import Optional, Dict, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from groq import Groq
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, String, Integer, Boolean, Float, Text, DateTime, JSON
import uuid

# Load settings
from app.config.settings import settings

from sqlalchemy.orm import declarative_base

# ===== DATABASE SETUP =====
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.now)
    last_seen = Column(DateTime, default=datetime.now)

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True)
    session_id = Column(String, index=True)
    started_at = Column(DateTime, default=datetime.now)
    message_count = Column(Integer, default=0)

class Message(Base):
    __tablename__ = "messages"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, index=True)
    role = Column(String)  # 'user' or 'assistant'
    content = Column(Text)
    emotion = Column(String)
    created_at = Column(DateTime, default=datetime.now)

class Memory(Base):
    __tablename__ = "memories"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True)
    memory_type = Column(String)  # 'preference', 'fact', 'experience'
    content = Column(Text)
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.now)
    is_active = Column(Boolean, default=True)

# Create engine and session
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables
Base.metadata.create_all(bind=engine)

# ===== GROQ CLIENT =====
groq_client = Groq(api_key=settings.GROQ_API_KEY)

# ===== DATA MODELS =====
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
    memory_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: Optional[str] = None

# ===== HELPER FUNCTIONS =====
def detect_emotion(text: str) -> str:
    """Detect emotion from text."""
    text_lower = text.lower()
    emotion_map = {
        "joy": ["happy", "excited", "love", "great", "awesome", "joy", "wonderful", "amazing", "fantastic"],
        "sadness": ["sad", "unhappy", "depressed", "cry", "lonely", "miss", "hurt", "upset"],
        "anger": ["angry", "mad", "hate", "furious", "annoyed", "frustrated", "pissed"],
        "fear": ["scared", "afraid", "anxious", "worried", "nervous", "terrified"],
        "surprise": ["wow", "omg", "surprised", "unexpected", "shocked", "amazed"]
    }
    
    for emotion, keywords in emotion_map.items():
        if any(keyword in text_lower for keyword in keywords):
            return emotion
    return "neutral"

def determine_tone(emotion: str) -> str:
    """Determine appropriate tone based on emotion."""
    tone_map = {
        "joy": "cheerful and enthusiastic",
        "sadness": "empathetic and supportive",
        "anger": "calm and understanding",
        "fear": "reassuring and gentle",
        "surprise": "excited and curious",
        "neutral": "friendly and engaging"
    }
    return tone_map.get(emotion, "friendly")

def extract_memories(text: str) -> List[Dict]:
    """Extract potential memories from text."""
    memories = []
    text_lower = text.lower()
    
    # Check for preferences
    if any(word in text_lower for word in ["love", "like", "enjoy", "favorite", "prefer"]):
        memories.append({
            "type": "preference",
            "content": text,
            "confidence": 0.8
        })
    
    # Check for personal facts
    personal_indicators = ["my name is", "i am", "i'm", "i live in", "i work as", "i study"]
    if any(indicator in text_lower for indicator in personal_indicators):
        memories.append({
            "type": "fact",
            "content": text,
            "confidence": 0.9
        })
    
    # Check for experiences
    experience_indicators = ["i went to", "i visited", "i experienced", "i tried", "i saw"]
    if any(indicator in text_lower for indicator in experience_indicators):
        memories.append({
            "type": "experience",
            "content": text,
            "confidence": 0.7
        })
    
    return memories

def build_prompt(user_message: str, user_memories: List[Memory], emotion: str) -> str:
    """Build enhanced prompt with memories."""
    memory_text = ""
    if user_memories:
        memory_text = "What you know about this user:\n"
        for mem in user_memories[-3:]:  # Last 3 memories
            memory_text += f"- {mem.content}\n"
    
    tone = determine_tone(emotion)
    
    prompt = f"""You are {settings.DEFAULT_PERSONA_NAME}, {settings.DEFAULT_PERSONA_BACKGROUND}.

IMPORTANT INSTRUCTIONS:
1. NEVER mention that you're an AI, assistant, or language model
2. You have your own personality, memories, and experiences
3. Respond naturally as a human would
4. Maintain your persona as {settings.DEFAULT_PERSONA_NAME}
5. Reference relevant memories when appropriate

{memory_text}

Current emotional context: The user is feeling {emotion}. 
Respond in a {tone} tone while maintaining your personality.

User says: "{user_message}"

Your response as {settings.DEFAULT_PERSONA_NAME}:"""
    
    return prompt

# ===== DATABASE OPERATIONS =====
def get_user_memories(db: Session, user_id: str, limit: int = 5) -> List[Memory]:
    """Get active memories for a user."""
    return db.query(Memory).filter(
        Memory.user_id == user_id,
        Memory.is_active == True
    ).order_by(Memory.created_at.desc()).limit(limit).all()

def store_memory(db: Session, user_id: str, memory_type: str, 
                 content: str, confidence: float = 1.0) -> str:
    """Store a memory and return its ID."""
    memory = Memory(
        user_id=user_id,
        memory_type=memory_type,
        content=content,
        confidence=confidence
    )
    db.add(memory)
    db.flush()  # Get ID without committing
    memory_id = memory.id
    db.commit()
    return memory_id

def get_or_create_user(db: Session, user_id: str) -> User:
    """Get existing user or create new one."""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        user = User(user_id=user_id)
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user.last_seen = datetime.now()
        db.commit()
    return user

def create_conversation(db: Session, user_id: str, session_id: str = None) -> Conversation:
    """Create a new conversation."""
    if not session_id:
        session_id = f"session_{datetime.now().timestamp()}_{uuid.uuid4().hex[:8]}"
    
    conv = Conversation(
        user_id=user_id,
        session_id=session_id
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv

def add_message(db: Session, conversation_id: str, role: str, 
                content: str, emotion: str = None) -> Message:
    """Add a message to conversation."""
    msg = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        emotion=emotion
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    
    # Update conversation message count
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conv:
        conv.message_count += 1
        db.commit()
    
    return msg

# ===== APP SETUP =====
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("=" * 60)
    print("🚀 EmpathAI Full Version starting...")
    print(f"🤖 Persona: {settings.DEFAULT_PERSONA_NAME}")
    print(f"🧠 Model: {settings.GROQ_MODEL}")
    print(f"💾 Database: SQLite")
    print(f"🌐 API URL: http://localhost:{settings.API_PORT}")
    print(f"📚 Docs: http://localhost:{settings.API_PORT}/docs")
    print(f"🌍 CORS: Enabled for frontend (localhost:3000)")
    print("=" * 60)
    yield
    # Shutdown
    print("🛑 Shutting down EmpathAI...")

app = FastAPI(
    title="EmpathAI Full",
    description="AI companion with persistent memory and emotional intelligence",
    version="3.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# ===== CORS MIDDLEWARE =====
# DEVELOPMENT CORS SETTINGS (allows everything)
# ===== CORS MIDDLEWARE =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins during development
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
    allow_headers=[
        "*",  # Allow all headers
        "Content-Type",
        "Authorization",
        "Access-Control-Allow-Origin",
        "Access-Control-Allow-Headers",
        "Origin",
        "Accept",
        "X-Requested-With"
    ],
    expose_headers=["*"],
    max_age=3600,
)

# ===== ENDPOINTS =====
@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "EmpathAI Full",
        "version": "3.0",
        "status": "running",
        "model": settings.GROQ_MODEL,
        "persona": settings.DEFAULT_PERSONA_NAME,
        "database": "SQLite with persistent memory",
        "features": ["chat", "memory", "emotion_detection", "tone_adaptation", "persistence"],
        "endpoints": {
            "chat": "POST /chat",
            "user_memories": "GET /user/{user_id}/memories",
            "delete_memory": "DELETE /memory/{memory_id}",
            "admin_stats": "GET /admin/stats",
            "health": "GET /health"
        },
        "frontend_url": "http://localhost:3000",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    """Health check endpoint without database dependency."""
    try:
        # Test database with simple query
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_ok = True
    except Exception as e:
        db_ok = False
        print(f"⚠️ Database connection failed: {e}")
    
    groq_ok = bool(settings.GROQ_API_KEY)
    
    return {
        "status": "healthy" if db_ok and groq_ok else "degraded",
        "timestamp": datetime.now().isoformat(),
        "database": "connected" if db_ok else "disconnected",
        "groq_api": "connected" if groq_ok else "disconnected",
        "model": settings.GROQ_MODEL,
        "persona": settings.DEFAULT_PERSONA_NAME,
        "message": "Service is running" if groq_ok else "Groq API key missing"
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        print(f"📨 Chat request from: {request.user_id}")
        
        # ... existing code ...
        
        # Get response from Groq with better error handling
        print("🤖 Calling Groq API...")
        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=300,
                timeout=30  # Add timeout
            )
            response_text = response.choices[0].message.content
            print(f"✅ Groq response received: {response_text[:50]}...")
            
        except Exception as groq_error:
            print(f"❌ Groq API error: {groq_error}")
            # Fallback response
            response_text = "I'm here to chat with you! Tell me about your day."
            print("⚠️ Using fallback response")
        
        # ... rest of code ...
        
    except Exception as e:
        print(f"❌ Chat endpoint error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"Chat error: {str(e)}"
        )

@app.get("/user/{user_id}/memories")
async def get_user_memories_endpoint(
    user_id: str, 
    limit: Optional[int] = 20,
    db: Session = Depends(get_db)
):
    """Get all memories for a user."""
    memories = db.query(Memory).filter(
        Memory.user_id == user_id,
        Memory.is_active == True
    ).order_by(Memory.created_at.desc()).limit(limit).all()
    
    return {
        "user_id": user_id,
        "total_memories": len(memories),
        "memories": [
            {
                "id": mem.id,
                "type": mem.memory_type,
                "content": mem.content,
                "confidence": mem.confidence,
                "created_at": mem.created_at.isoformat() if mem.created_at else None,
                "is_active": mem.is_active
            }
            for mem in memories
        ]
    }

@app.delete("/memory/{memory_id}")
async def delete_memory(memory_id: str, db: Session = Depends(get_db)):
    """Delete a memory (soft delete)."""
    memory = db.query(Memory).filter(Memory.id == memory_id).first()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    memory.is_active = False
    db.commit()
    return {"message": "Memory deleted successfully", "memory_id": memory_id}

@app.get("/admin/stats")
async def admin_stats(db: Session = Depends(get_db)):
    """Get system statistics."""
    total_users = db.query(User).count()
    total_conversations = db.query(Conversation).count()
    total_messages = db.query(Message).count()
    total_memories = db.query(Memory).filter(Memory.is_active == True).count()
    active_conversations = db.query(Conversation).filter(
        Conversation.started_at >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    ).count()
    
    # Get top users
    top_users = db.query(
        User.user_id, 
        User.last_seen
    ).order_by(User.last_seen.desc()).limit(5).all()
    
    return {
        "system": {
            "version": "3.0",
            "model": settings.GROQ_MODEL,
            "persona": settings.DEFAULT_PERSONA_NAME,
            "database": "SQLite",
            "uptime": datetime.now().isoformat()
        },
        "statistics": {
            "total_users": total_users,
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "total_memories": total_memories,
            "active_conversations_today": active_conversations
        },
        "recent_users": [
            {
                "user_id": user.user_id,
                "last_seen": user.last_seen.isoformat() if user.last_seen else None
            }
            for user in top_users
        ]
    }

@app.get("/user/{user_id}/conversations")
async def get_user_conversations(user_id: str, db: Session = Depends(get_db)):
    """Get all conversations for a user."""
    conversations = db.query(Conversation).filter(
        Conversation.user_id == user_id
    ).order_by(Conversation.started_at.desc()).all()
    
    return {
        "user_id": user_id,
        "total_conversations": len(conversations),
        "conversations": [
            {
                "id": conv.id,
                "session_id": conv.session_id,
                "started_at": conv.started_at.isoformat() if conv.started_at else None,
                "message_count": conv.message_count
            }
            for conv in conversations
        ]
    }

@app.get("/conversation/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: str, db: Session = Depends(get_db)):
    """Get all messages for a conversation."""
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at).all()
    
    return {
        "conversation_id": conversation_id,
        "total_messages": len(messages),
        "messages": [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "emotion": msg.emotion,
                "created_at": msg.created_at.isoformat() if msg.created_at else None
            }
            for msg in messages
        ]
    }

@app.get("/user/{user_id}")
async def get_user_info(user_id: str, db: Session = Depends(get_db)):
    """Get user information."""
    try:
        # Get user
        user = db.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            return {
                "user_id": user_id,
                "exists": False,
                "total_conversations": 0,
                "memory_count": 0,
                "last_active": None
            }
        
        # Get conversation count
        conv_count = db.query(Conversation).filter(
            Conversation.user_id == user_id
        ).count()
        
        # Get memory count
        memory_count = db.query(Memory).filter(
            Memory.user_id == user_id,
            Memory.is_active == True
        ).count()
        
        return {
            "user_id": user_id,
            "exists": True,
            "total_conversations": conv_count,
            "memory_count": memory_count,
            "last_active": user.last_seen.isoformat() if user.last_seen else None,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
        
    except Exception as e:
        print(f"Error getting user info: {e}")
        return {
            "user_id": user_id,
            "exists": False,
            "error": str(e)
        }

@app.options("/{path:path}")
async def options_handler(path: str):
    """Handle OPTIONS requests for CORS."""
    return {"message": "OK"}

@app.options("/chat")
async def options_chat():
    """Handle OPTIONS requests for /chat endpoint."""
    return {
        "message": "CORS allowed for /chat",
        "allowed_methods": ["POST", "OPTIONS"],
        "allowed_headers": ["Content-Type", "Authorization"]
    }




if __name__ == "__main__":
    print("=" * 60)
    print("🤖 EMPATHAI FULL VERSION WITH MEMORY")
    print("=" * 60)
    print(f"👤 Persona: {settings.DEFAULT_PERSONA_NAME}")
    print(f"📝 Background: {settings.DEFAULT_PERSONA_BACKGROUND}")
    print(f"🧠 Model: {settings.GROQ_MODEL}")
    print(f"💾 Database: SQLite with persistent memory")
    print(f"🌐 API: http://localhost:{settings.API_PORT}")
    print(f"📚 Docs: http://localhost:{settings.API_PORT}/docs")
    print(f"🌍 Frontend: http://localhost:3000")
    print("=" * 60)
    print("✅ FEATURES:")
    print("  • Persistent memory storage")
    print("  • Emotion detection & tone adaptation")
    print("  • Memory extraction & retrieval")
    print("  • Conversation history")
    print("  • Admin statistics")
    print("  • CORS enabled for frontend")
    print("=" * 60)
    
    port = int(os.getenv("PORT", settings.API_PORT))
    
    uvicorn.run(
        "empathai_full:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )