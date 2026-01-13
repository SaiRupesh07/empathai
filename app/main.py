# app/main.py - Complete version with PostgreSQL memory system
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from google import genai
from sqlalchemy.orm import Session

# Import our modules
from app.database.postgres import get_db, init_database
from app.memory.memory_manager import memory_manager
from app.config import settings  # Use your existing config

# Check for API key
if not settings.gemini_api_key or settings.gemini_api_key.startswith("AIzaSyYour"):
    print("❌ ERROR: Gemini API key not set!")
    print("Get free API key from: https://aistudio.google.com/app/apikey")
    print("Then edit .env file")
    exit(1)

# Initialize Gemini
try:
    # Create client directly
    client = genai.Client(api_key=settings.gemini_api_key)
    print("✅ Gemini API configured successfully")
except Exception as e:
    print(f"❌ Gemini configuration failed: {e}")
    exit(1)

# Create FastAPI app
app = FastAPI(
    title="EmpathAI Chatbot",
    description="Human-like conversational AI with long-term memory",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Request/Response models
class ChatRequest(BaseModel):
    user_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    user_id: str

# ===== STARTUP EVENT =====
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    try:
        init_database()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")

# ===== API ENDPOINTS =====
@app.get("/")
async def root():
    return {
        "service": settings.app_name,
        "status": "running",
        "version": "1.0.0",
        "environment": settings.app_env,
        "features": ["long-term-memory", "emotional-intelligence", "consistent-persona"],
        "persona": {
            "name": settings.persona_name,
            "age": settings.persona_age,
            "background": settings.persona_background
        },
        "docs": "/docs",
        "health": "/health"
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """Main chat endpoint with memory integration."""
    try:
        # Get or create user in database
        user = memory_manager.get_or_create_user(db, request.user_id)
        
        # Create new conversation session
        conversation = memory_manager.create_conversation(db, request.user_id)
        
        # Get relevant memories from long-term storage
        memories = memory_manager.get_relevant_memories(db, request.user_id, request.message)
        memory_context = ""
        if memories:
            memory_context = "Things I remember about you:\n"
            for memory in memories:
                memory_context += f"• {memory.content}\n"
        
        # Get conversation history
        history = memory_manager.get_conversation_history(db, request.user_id)
        conversation_history = ""
        if history:
            conversation_history = "Recent conversation:\n"
            for h in history[-settings.short_term_memory_size:]:  # Use config
                conversation_history += f"{h['role'].title()}: {h['content']}\n"
        
        # Get persona settings (preferred tone, style, etc.)
        persona_settings = memory_manager.get_persona_settings(db, request.user_id)
        
        # Build enhanced prompt with memory and persona
        prompt = f"""You are {settings.persona_name}, {settings.persona_background}.
You're having a conversation with a friend.

IMPORTANT RULES:
1. You are human - never mention being an AI, model, or assistant
2. Be {persona_settings.preferred_tone} and {persona_settings.communication_style}
3. If you don't know something, admit it naturally
4. Never make up facts about the user or yourself
5. Adapt your tone to match the conversation
6. Keep responses under {settings.max_tokens} tokens

{memory_context}

{conversation_history}

User: {request.message}

{settings.persona_name}:"""
        
        # Generate response using Gemini
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config={
                "temperature": settings.temperature,
                "max_output_tokens": settings.max_tokens
            }
        )
        
        # Store user message in database
        memory_manager.add_message(
            db, 
            str(conversation.id), 
            "user", 
            request.message
        )
        
        # Store bot response in database
        memory_manager.add_message(
            db, 
            str(conversation.id), 
            "assistant", 
            response.text
        )
        
        # Extract and store important information as long-term memories
        memory_manager.extract_and_store_memories(
            db, 
            request.user_id, 
            request.message, 
            response.text,
            source_conversation=str(conversation.id)
        )
        
        # Update conversation summary periodically
        messages_count = len(history)
        if messages_count >= settings.summary_window_size and messages_count % settings.summary_window_size == 0:
            summary = memory_manager.summarize_conversation(db, str(conversation.id))
            conversation.summary = summary
            db.commit()
        
        return ChatResponse(
            response=response.text,
            user_id=request.user_id
        )
        
    except Exception as e:
        # Log error but return user-friendly message
        print(f"❌ Error in chat endpoint: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"I'm having trouble processing that. Please try again."
        )

@app.get("/memory/{user_id}")
async def get_user_memory(user_id: str, db: Session = Depends(get_db)):
    """Get all stored memories for a user."""
    try:
        # Get long-term memories
        memories = memory_manager.get_relevant_memories(db, user_id, limit=20)
        
        # Get conversation history
        history = memory_manager.get_conversation_history(db, user_id, limit=20)
        
        # Get persona settings
        persona = memory_manager.get_persona_settings(db, user_id)
        
        return {
            "user_id": user_id,
            "long_term_memories": [
                {
                    "id": str(mem.id),
                    "type": mem.memory_type,
                    "content": mem.content,
                    "confidence": mem.confidence,
                    "created_at": mem.created_at.isoformat() if mem.created_at else None
                }
                for mem in memories
            ],
            "conversation_history": history,
            "persona_settings": {
                "preferred_tone": persona.preferred_tone,
                "communication_style": persona.communication_style,
                "topics_of_interest": persona.topics_of_interest,
                "trust_level": persona.trust_level
            },
            "memory_count": len(memories),
            "conversation_count": len(history)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health(db: Session = Depends(get_db)):
    """Comprehensive health check endpoint."""
    try:
        # Check database connection
        db.execute("SELECT 1")
        db_status = "connected"
        
        # Check memory manager
        memory_status = "ready" if memory_manager.embedding_model else "embeddings_failed"
        
        # Count users
        from app.memory.models import User
        user_count = db.query(User).count()
        
        # Count memories
        from app.memory.models import LongTermMemory
        memory_count = db.query(LongTermMemory).count()
        
        return {
            "status": "healthy",
            "app": settings.app_name,
            "environment": settings.app_env,
            "database": db_status,
            "gemini": "configured",
            "memory_system": memory_status,
            "statistics": {
                "users": user_count,
                "memories": memory_count
            }
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "database": "disconnected",
            "gemini": "unknown"
        }

@app.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get system statistics."""
    from app.memory.models import User, Conversation, LongTermMemory, Message
    
    stats = {
        "users": db.query(User).count(),
        "conversations": db.query(Conversation).count(),
        "messages": db.query(Message).count(),
        "memories": db.query(LongTermMemory).count(),
        "active_memories": db.query(LongTermMemory).filter(LongTermMemory.is_active == True).count()
    }
    
    return stats

@app.get("/config")
async def get_config():
    """Get current configuration (without sensitive data)."""
    return {
        "app_name": settings.app_name,
        "app_env": settings.app_env,
        "persona": {
            "name": settings.persona_name,
            "age": settings.persona_age
        },
        "memory": {
            "short_term_size": settings.short_term_memory_size,
            "summary_window": settings.summary_window_size,
            "embedding_model": settings.embedding_model
        },
        "gemini": {
            "model": settings.gemini_model,
            "max_tokens": settings.max_tokens,
            "temperature": settings.temperature
        }
    }

# ===== DEBUG ENDPOINTS =====
@app.get("/debug/users")
async def debug_users(db: Session = Depends(get_db)):
    """Debug endpoint to list all users."""
    from app.memory.models import User
    users = db.query(User).all()
    
    return {
        "users": [
            {
                "id": str(user.id),
                "user_id": user.user_id,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_seen": user.last_seen.isoformat() if user.last_seen else None
            }
            for user in users
        ],
        "count": len(users)
    }

@app.delete("/debug/reset/{user_id}")
async def reset_user_data(user_id: str, db: Session = Depends(get_db)):
    """Reset all data for a user (debug only)."""
    from app.memory.models import LongTermMemory, PersonaSettings
    
    # Delete memories
    memory_count = db.query(LongTermMemory).filter(LongTermMemory.user_id == user_id).delete()
    
    # Reset persona settings
    persona = db.query(PersonaSettings).filter(PersonaSettings.user_id == user_id).first()
    if persona:
        persona.preferred_tone = "casual"
        persona.communication_style = "balanced"
        persona.trust_level = 50
    
    db.commit()
    
    return {
        "message": f"Reset data for user {user_id}",
        "memories_deleted": memory_count
    }

# For development - create some test data
@app.post("/test/setup")
async def setup_test_data(db: Session = Depends(get_db)):
    """Create test user with some memories."""
    test_user_id = "test_user_001"
    
    # Create user
    user = memory_manager.get_or_create_user(db, test_user_id)
    
    # Add some test memories
    test_memories = [
        ("fact", f"I am a software developer interested in {settings.app_name}"),
        ("preference", "I love South Indian food, especially dosa"),
        ("preference", "I enjoy watching sci-fi movies"),
        ("fact", "I have a dog named Max"),
        ("event", "I went hiking last weekend in the mountains")
    ]
    
    for mem_type, content in test_memories:
        memory_manager.store_memory(db, test_user_id, mem_type, content)
    
    return {
        "message": "Test data created",
        "user_id": test_user_id,
        "memories_added": len(test_memories),
        "persona": settings.persona_name
    }