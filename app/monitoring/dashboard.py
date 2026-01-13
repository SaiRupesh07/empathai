from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import psutil
import os

from app.database.postgres import get_db
from app.memory.models import User, Conversation, Message, LongTermMemory

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/dashboard")
async def admin_dashboard(db: Session = Depends(get_db)):
    """Admin dashboard with system metrics."""
    
    # System metrics
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Database metrics
    total_users = db.query(func.count(User.id)).scalar()
    total_conversations = db.query(func.count(Conversation.id)).scalar()
    total_messages = db.query(func.count(Message.id)).scalar()
    total_memories = db.query(func.count(LongTermMemory.id)).scalar()
    
    # Recent activity
    last_hour = datetime.utcnow() - timedelta(hours=1)
    recent_users = db.query(func.count(User.id)).filter(
        User.last_seen >= last_hour
    ).scalar()
    
    recent_conversations = db.query(func.count(Conversation.id)).filter(
        Conversation.started_at >= last_hour
    ).scalar()
    
    # Memory statistics
    memory_stats = db.query(
        LongTermMemory.category,
        func.count(LongTermMemory.id).label('count'),
        func.avg(LongTermMemory.confidence).label('avg_confidence')
    ).filter(
        LongTermMemory.is_active == True
    ).group_by(LongTermMemory.category).all()
    
    # Top users by activity
    top_users = db.query(
        User.user_id,
        func.count(Conversation.id).label('conversation_count'),
        func.count(Message.id).label('message_count')
    ).join(Conversation).join(Message).group_by(
        User.user_id
    ).order_by(desc('message_count')).limit(10).all()
    
    return {
        "system": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "disk_percent": disk.percent,
            "uptime": psutil.boot_time(),
            "process_memory_mb": psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        },
        "database": {
            "total_users": total_users,
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "total_memories": total_memories,
            "recent_users_last_hour": recent_users,
            "recent_conversations_last_hour": recent_conversations
        },
        "memory_statistics": [
            {
                "category": stat.category,
                "count": stat.count,
                "avg_confidence": float(stat.avg_confidence or 0)
            }
            for stat in memory_stats
        ],
        "top_users": [
            {
                "user_id": user.user_id,
                "conversation_count": user.conversation_count,
                "message_count": user.message_count
            }
            for user in top_users
        ],
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/user/{user_id}")
async def user_analytics(user_id: str, db: Session = Depends(get_db)):
    """Get detailed analytics for a specific user."""
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        return {"error": "User not found"}
    
    # User conversations
    conversations = db.query(Conversation).filter(
        Conversation.user_id == user_id
    ).order_by(desc(Conversation.started_at)).limit(20).all()
    
    # User memories
    memories = db.query(LongTermMemory).filter(
        LongTermMemory.user_id == user_id,
        LongTermMemory.is_active == True
    ).order_by(desc(LongTermMemory.importance)).limit(50).all()
    
    # Memory categories
    memory_categories = db.query(
        LongTermMemory.category,
        func.count(LongTermMemory.id).label('count')
    ).filter(
        LongTermMemory.user_id == user_id,
        LongTermMemory.is_active == True
    ).group_by(LongTermMemory.category).all()
    
    return {
        "user_info": {
            "user_id": user.user_id,
            "username": user.username,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_seen": user.last_seen.isoformat() if user.last_seen else None,
            "conversation_count": user.conversation_count,
            "total_messages": user.total_messages
        },
        "recent_conversations": [
            {
                "id": str(conv.id),
                "started_at": conv.started_at.isoformat() if conv.started_at else None,
                "message_count": conv.message_count,
                "dominant_sentiment": conv.dominant_sentiment
            }
            for conv in conversations
        ],
        "memory_statistics": {
            "total_memories": len(memories),
            "categories": [
                {"category": cat.category, "count": cat.count}
                for cat in memory_categories
            ],
            "avg_confidence": db.query(
                func.avg(LongTermMemory.confidence)
            ).filter(
                LongTermMemory.user_id == user_id,
                LongTermMemory.is_active == True
            ).scalar() or 0
        },
        "top_memories": [
            {
                "id": str(mem.id),
                "type": mem.memory_type,
                "category": mem.category.value if mem.category else None,
                "content": mem.content[:100] + "..." if len(mem.content) > 100 else mem.content,
                "confidence": mem.confidence,
                "importance": mem.importance,
                "last_accessed": mem.last_accessed.isoformat() if mem.last_accessed else None
            }
            for mem in memories[:10]
        ]
    }