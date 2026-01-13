import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import logging
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_, text
import numpy as np
from sentence_transformers import SentenceTransformer
import hashlib

from app.memory.models import (
    User, Conversation, Message, LongTermMemory, PersonaSettings,
    MemoryCategory, MemoryPriority
)
from app.database.postgres import get_db
from app.config import settings

logger = logging.getLogger(__name__)

class MemoryManager:
    def __init__(self):
        self.embedding_model = None
        self.memory_cache = {}  # LRU cache for frequently accessed memories
        self._init_embeddings()
        self._init_memory_categories()
    
    def _init_embeddings(self):
        """Initialize embedding model."""
        try:
            if hasattr(settings, 'embedding_model') and settings.embedding_model:
                self.embedding_model = SentenceTransformer(settings.embedding_model)
                logger.info(f"✅ Embedding model loaded: {settings.embedding_model}")
            else:
                # Use a lightweight default if not specified
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("✅ Loaded default embedding model: all-MiniLM-L6-v2")
        except Exception as e:
            logger.error(f"❌ Failed to load embedding model: {e}")
            self.embedding_model = None
    
    def _init_memory_categories(self):
        """Initialize memory category definitions."""
        self.memory_categories = {
            "preference": {
                "keywords": ["like", "love", "enjoy", "favorite", "prefer", "hate", "dislike", "fond of"],
                "lifespan_days": 365,  # 1 year
                "priority": MemoryPriority.HIGH
            },
            "fact": {
                "keywords": ["am", "'m", "have", "work", "study", "live", "born", "age", "from"],
                "lifespan_days": 730,  # 2 years
                "priority": MemoryPriority.MEDIUM
            },
            "experience": {
                "keywords": ["went to", "visited", "experienced", "happened", "once"],
                "lifespan_days": 180,  # 6 months
                "priority": MemoryPriority.MEDIUM
            },
            "goal": {
                "keywords": ["want to", "plan to", "goal", "aspire", "dream", "hope to"],
                "lifespan_days": 90,  # 3 months
                "priority": MemoryPriority.HIGH
            },
            "emotion": {
                "keywords": ["feel", "felt", "emotion", "happy", "sad", "angry", "excited"],
                "lifespan_days": 30,  # 1 month
                "priority": MemoryPriority.LOW
            }
        }
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding vector for text."""
        if not self.embedding_model or not text:
            return None
        
        try:
            # Normalize text
            text = text.strip()
            if len(text) < 3:
                return None
            
            embedding = self.embedding_model.encode([text], normalize_embeddings=True)[0]
            return embedding.tolist()
        except Exception as e:
            logger.error(f"❌ Failed to generate embedding: {e}")
            return None
    
    def calculate_memory_hash(self, user_id: str, content: str) -> str:
        """Calculate unique hash for memory to prevent duplicates."""
        hash_string = f"{user_id}:{content.lower().strip()}"
        return hashlib.md5(hash_string.encode()).hexdigest()
    
    # ===== USER MANAGEMENT =====
    def get_or_create_user(self, db: Session, user_id: str) -> User:
        """Get existing user or create new one."""
        user = db.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            user = User(
                user_id=user_id,
                last_seen=datetime.utcnow(),
                metadata={
                    "created_at": datetime.utcnow().isoformat(),
                    "created_via": "chat",
                    "conversation_count": 0,
                    "total_messages": 0
                }
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"✅ Created new user: {user_id}")
        else:
            # Update last seen
            user.last_seen = datetime.utcnow()
            
            # Update metadata
            if not user.metadata:
                user.metadata = {}
            user.metadata["last_seen"] = datetime.utcnow().isoformat()
            
            db.commit()
        
        return user
    
    # ===== CONVERSATION MANAGEMENT =====
    def create_conversation(self, db: Session, user_id: str, session_id: str = None) -> Conversation:
        """Create a new conversation session."""
        conversation = Conversation(
            user_id=user_id,
            session_id=session_id or f"session_{datetime.utcnow().timestamp()}_{hashlib.md5(user_id.encode()).hexdigest()[:8]}",
            metadata={
                "created_at": datetime.utcnow().isoformat(),
                "message_count": 0
            }
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        logger.info(f"✅ Created conversation: {conversation.id} for user {user_id}")
        return conversation
    
    def add_message(self, db: Session, conversation_id: str, role: str, content: str, 
                   sentiment: str = None, emotion: Dict = None) -> Message:
        """Add a message to conversation."""
        embedding = self.get_embedding(content)
        
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            sentiment=sentiment,
            emotion_data=json.dumps(emotion) if emotion else None,
            embedding=json.dumps(embedding) if embedding else None,
            metadata={
                "length": len(content),
                "word_count": len(content.split()),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        
        # Update conversation metadata
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conversation and conversation.metadata:
            conversation.metadata["message_count"] = conversation.metadata.get("message_count", 0) + 1
            db.commit()
        
        # Update user metadata
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conversation:
            user = db.query(User).filter(User.user_id == conversation.user_id).first()
            if user and user.metadata:
                user.metadata["total_messages"] = user.metadata.get("total_messages", 0) + 1
                db.commit()
        
        return message
    
    def get_conversation_history(self, db: Session, user_id: str, limit: int = 10, 
                                include_current: bool = True) -> List[Dict]:
        """Get recent conversation history for user."""
        query = db.query(Conversation).filter(Conversation.user_id == user_id)
        
        if not include_current:
            # Get only completed conversations
            query = query.filter(Conversation.ended_at.isnot(None))
        
        conversations = query.order_by(desc(Conversation.started_at)).limit(5).all()
        
        history = []
        for conv in conversations:
            messages = db.query(Message).filter(
                Message.conversation_id == conv.id
            ).order_by(Message.created_at).limit(20).all()
            
            conv_history = [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "time": msg.created_at.isoformat() if msg.created_at else None,
                    "sentiment": msg.sentiment,
                    "emotion": json.loads(msg.emotion_data) if msg.emotion_data else None
                }
                for msg in messages
            ]
            history.extend(conv_history)
        
        # Return last N messages, preserving chronological order
        return history[-limit:] if len(history) > limit else history
    
    # ===== LONG-TERM MEMORY =====
    def store_memory(self, db: Session, user_id: str, memory_type: str, content: str, 
                    confidence: float = 1.0, source_conversation: str = None,
                    category: str = None, importance: float = 0.5) -> Optional[LongTermMemory]:
        """Store a long-term memory with deduplication."""
        # Check for duplicates
        memory_hash = self.calculate_memory_hash(user_id, content)
        existing = db.query(LongTermMemory).filter(
            LongTermMemory.user_id == user_id,
            LongTermMemory.memory_hash == memory_hash
        ).first()
        
        if existing:
            # Update existing memory
            existing.confidence = max(existing.confidence, confidence)
            existing.importance = max(existing.importance, importance)
            existing.updated_at = datetime.utcnow()
            existing.access_count = existing.access_count + 1 if existing.access_count else 1
            db.commit()
            db.refresh(existing)
            logger.debug(f"✅ Updated existing memory: {memory_type} for {user_id}")
            return existing
        
        # Determine category if not provided
        if not category:
            category = self._categorize_memory(content, memory_type)
        
        # Determine lifespan based on category
        lifespan_days = self.memory_categories.get(category, {}).get("lifespan_days", 30)
        
        embedding = self.get_embedding(content)
        
        memory = LongTermMemory(
            user_id=user_id,
            memory_type=memory_type,
            category=category,
            content=content,
            memory_hash=memory_hash,
            embedding=json.dumps(embedding) if embedding else None,
            confidence=confidence,
            importance=importance,
            source_conversation=source_conversation,
            access_count=1,
            expires_at=datetime.utcnow() + timedelta(days=lifespan_days),
            metadata={
                "created_via": "auto_extract",
                "original_length": len(content),
                "category_confidence": confidence
            }
        )
        db.add(memory)
        db.commit()
        db.refresh(memory)
        
        logger.info(f"✅ Stored {memory_type} ({category}) memory for {user_id}: {content[:50]}...")
        
        # Add to cache
        cache_key = f"{user_id}:{memory.id}"
        self.memory_cache[cache_key] = {
            "content": content,
            "type": memory_type,
            "category": category,
            "confidence": confidence,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Limit cache size
        if len(self.memory_cache) > 1000:
            # Remove oldest entry
            oldest_key = next(iter(self.memory_cache))
            del self.memory_cache[oldest_key]
        
        return memory
    
    def _categorize_memory(self, content: str, memory_type: str) -> str:
        """Automatically categorize memory based on content."""
        content_lower = content.lower()
        
        for category, config in self.memory_categories.items():
            for keyword in config["keywords"]:
                if keyword in content_lower:
                    return category
        
        # Default categories based on memory_type
        type_to_category = {
            "preference": "preference",
            "fact": "fact",
            "experience": "experience",
            "goal": "goal",
            "emotion": "emotion"
        }
        
        return type_to_category.get(memory_type, "general")
    
    def get_relevant_memories(self, db: Session, user_id: str, query: str = None, 
                             limit: int = 5, min_confidence: float = 0.3) -> List[Dict]:
        """Get relevant memories for a user with advanced filtering."""
        # Try cache first
        if not query:
            cache_key = f"{user_id}:recent"
            if cache_key in self.memory_cache:
                logger.debug(f"Using cached memories for {user_id}")
                return self.memory_cache[cache_key]
        
        base_query = db.query(LongTermMemory).filter(
            LongTermMemory.user_id == user_id,
            LongTermMemory.is_active == True,
            LongTermMemory.confidence >= min_confidence,
            or_(
                LongTermMemory.expires_at.is_(None),
                LongTermMemory.expires_at > datetime.utcnow()
            )
        )
        
        memories = []
        
        if query and self.embedding_model:
            try:
                # Try semantic search first
                query_embedding = self.get_embedding(query)
                if query_embedding:
                    # Convert to PostgreSQL vector query if using pgvector
                    if hasattr(db.bind.url, 'drivername') and 'postgresql' in db.bind.url.drivername:
                        # Use pgvector similarity search
                        results = db.execute(text("""
                            SELECT id, content, memory_type, category, confidence,
                                   (embedding <=> CAST(:embedding AS vector)) as distance
                            FROM long_term_memory
                            WHERE user_id = :user_id AND is_active = true 
                            AND confidence >= :min_confidence
                            ORDER BY distance
                            LIMIT :limit
                        """), {
                            "embedding": query_embedding,
                            "user_id": user_id,
                            "min_confidence": min_confidence,
                            "limit": limit
                        }).fetchall()
                        
                        memories = [
                            {
                                "id": r[0],
                                "content": r[1],
                                "type": r[2],
                                "category": r[3],
                                "confidence": r[4],
                                "relevance_score": 1.0 - float(r[5])  # Convert distance to similarity
                            }
                            for r in results
                        ]
                
                if not memories:
                    # Fall back to keyword search
                    memories = base_query.filter(
                        or_(
                            LongTermMemory.content.ilike(f"%{query}%"),
                            LongTermMemory.category.ilike(f"%{query}%"),
                            LongTermMemory.memory_type.ilike(f"%{query}%")
                        )
                    ).order_by(
                        desc(LongTermMemory.importance),
                        desc(LongTermMemory.confidence),
                        desc(LongTermMemory.access_count)
                    ).limit(limit).all()
                    
                    memories = [self._memory_to_dict(m) for m in memories]
                    
            except Exception as e:
                logger.error(f"❌ Semantic search failed: {e}")
                # Fall back to simple query
                memories = base_query.order_by(
                    desc(LongTermMemory.importance),
                    desc(LongTermMemory.confidence)
                ).limit(limit).all()
                memories = [self._memory_to_dict(m) for m in memories]
        else:
            # Get most relevant memories (importance + recency)
            memories = base_query.order_by(
                desc(LongTermMemory.importance),
                desc(LongTermMemory.updated_at),
                desc(LongTermMemory.confidence)
            ).limit(limit).all()
            memories = [self._memory_to_dict(m) for m in memories]
        
        # Update access counts
        for memory_dict in memories:
            if "id" in memory_dict:
                memory = db.query(LongTermMemory).filter(LongTermMemory.id == memory_dict["id"]).first()
                if memory:
                    memory.access_count = (memory.access_count or 0) + 1
                    memory.last_accessed = datetime.utcnow()
        
        db.commit()
        
        # Cache the results
        if not query:
            self.memory_cache[f"{user_id}:recent"] = memories
        
        return memories
    
    def _memory_to_dict(self, memory: LongTermMemory) -> Dict:
        """Convert memory object to dictionary."""
        return {
            "id": memory.id,
            "content": memory.content,
            "type": memory.memory_type,
            "category": memory.category,
            "confidence": memory.confidence,
            "importance": memory.importance,
            "created_at": memory.created_at.isoformat() if memory.created_at else None,
            "access_count": memory.access_count or 0,
            "source": memory.source_conversation
        }
    
    def extract_and_store_memories(self, db: Session, user_id: str, user_message: str, 
                                  ai_response: str, conversation_id: str = None):
        """Extract and store memories from conversation with improved logic."""
        memories_to_store = []
        
        # Analyze user message for memories
        user_memories = self._analyze_text_for_memories(user_message, "user")
        for memory_type, content, confidence in user_memories:
            memories_to_store.append((memory_type, content, confidence))
        
        # Analyze AI response for user preferences mentioned
        ai_memories = self._analyze_text_for_memories(ai_response, "ai")
        for memory_type, content, confidence in ai_memories:
            memories_to_store.append((memory_type, content, confidence * 0.8))  # Lower confidence for AI-extracted
        
        # Store unique memories
        stored_count = 0
        for memory_type, content, confidence in memories_to_store:
            if confidence > 0.4:  # Minimum confidence threshold
                memory = self.store_memory(
                    db, user_id, memory_type, content, confidence, conversation_id
                )
                if memory:
                    stored_count += 1
        
        logger.info(f"✅ Extracted {stored_count} memories from conversation for {user_id}")
        return stored_count
    
    def _analyze_text_for_memories(self, text: str, source: str) -> List[Tuple[str, str, float]]:
        """Analyze text to extract potential memories with confidence scores."""
        memories = []
        text_lower = text.lower()
        sentences = self._split_into_sentences(text)
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            confidence = 1.0
            
            # Check for different memory types
            for category, config in self.memory_categories.items():
                for keyword in config["keywords"]:
                    if keyword in sentence_lower:
                        # Adjust confidence based on sentence structure
                        if source == "user":
                            if sentence_lower.startswith("i ") or "my " in sentence_lower:
                                confidence = 0.9
                            else:
                                confidence = 0.6
                        else:
                            confidence = 0.5  # Lower confidence for AI statements
                        
                        memories.append((category, sentence.strip(), confidence))
                        break
        
        return memories
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Simple sentence splitting."""
        import re
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    # ===== PERSONA SETTINGS =====
    def get_persona_settings(self, db: Session, user_id: str) -> PersonaSettings:
        """Get or create persona settings for user."""
        settings = db.query(PersonaSettings).filter(PersonaSettings.user_id == user_id).first()
        
        if not settings:
            # Get default settings
            default_settings = db.query(PersonaSettings).filter(
                PersonaSettings.user_id == "system_default"
            ).first()
            
            if default_settings:
                # Copy default settings
                settings = PersonaSettings(
                    user_id=user_id,
                    preferred_tone=default_settings.preferred_tone,
                    communication_style=default_settings.communication_style,
                    topics_of_interest=default_settings.topics_of_interest.copy(),
                    dislikes=default_settings.dislikes.copy(),
                    trust_level=default_settings.trust_level,
                    personality_traits=default_settings.personality_traits.copy(),
                    learning_preferences=default_settings.learning_preferences.copy(),
                    metadata={
                        "inherited_from": "system_default",
                        "created_at": datetime.utcnow().isoformat()
                    }
                )
            else:
                # Create with intelligent defaults based on initial conversation
                settings = PersonaSettings(
                    user_id=user_id,
                    preferred_tone="casual",
                    communication_style="balanced",
                    topics_of_interest=["general", "technology", "life"],
                    dislikes=["offensive_content", "spam"],
                    trust_level=50,
                    personality_traits=["friendly", "helpful", "curious"],
                    learning_preferences=["visual", "conversational"],
                    metadata={
                        "auto_generated": True,
                        "created_at": datetime.utcnow().isoformat()
                    }
                )
            
            db.add(settings)
            db.commit()
            db.refresh(settings)
            logger.info(f"✅ Created persona settings for user: {user_id}")
        
        return settings
    
    def update_persona_from_conversation(self, db: Session, user_id: str, 
                                        conversation_history: List[Dict]):
        """Update persona settings based on conversation patterns."""
        settings = self.get_persona_settings(db, user_id)
        
        # Analyze conversation for preferences
        all_messages = " ".join([msg.get("content", "") for msg in conversation_history])
        all_messages_lower = all_messages.lower()
        
        # Detect preferred topics
        topic_keywords = {
            "technology": ["code", "program", "computer", "tech", "software", "ai", "machine learning"],
            "art": ["art", "paint", "draw", "design", "creative", "music", "photo"],
            "sports": ["sport", "game", "team", "play", "exercise", "fitness"],
            "science": ["science", "research", "discover", "experiment", "theory"],
            "business": ["business", "work", "job", "career", "company", "market"]
        }
        
        detected_topics = []
        for topic, keywords in topic_keywords.items():
            if any(keyword in all_messages_lower for keyword in keywords):
                if topic not in settings.topics_of_interest:
                    detected_topics.append(topic)
        
        if detected_topics:
            settings.topics_of_interest.extend(detected_topics)
            # Remove duplicates
            settings.topics_of_interest = list(set(settings.topics_of_interest))
        
        # Detect tone preference
        emotional_words = ["love", "hate", "excited", "angry", "happy", "sad"]
        casual_words = ["hey", "yo", "lol", "haha", "omg"]
        formal_words = ["please", "thank you", "sincerely", "regards"]
        
        emotional_count = sum(1 for word in emotional_words if word in all_messages_lower)
        casual_count = sum(1 for word in casual_words if word in all_messages_lower)
        formal_count = sum(1 for word in formal_words if word in all_messages_lower)
        
        if casual_count > formal_count and casual_count > 2:
            settings.preferred_tone = "casual"
        elif formal_count > casual_count and formal_count > 2:
            settings.preferred_tone = "formal"
        elif emotional_count > 3:
            settings.preferred_tone = "empathetic"
        
        # Update trust level based on conversation length
        conversation_count = len(conversation_history)
        if conversation_count > 20:
            settings.trust_level = min(100, settings.trust_level + 10)
        
        # Update metadata
        if not settings.metadata:
            settings.metadata = {}
        settings.metadata["last_updated"] = datetime.utcnow().isoformat()
        settings.metadata["conversations_analyzed"] = conversation_count // 2
        
        db.commit()
        logger.info(f"✅ Updated persona for {user_id}: tone={settings.preferred_tone}, topics={len(settings.topics_of_interest)}")
        
        return settings
    
    def update_persona_settings(self, db: Session, user_id: str, **kwargs):
        """Update persona settings."""
        settings = self.get_persona_settings(db, user_id)
        
        for key, value in kwargs.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        
        settings.updated_at = datetime.utcnow()
        if not settings.metadata:
            settings.metadata = {}
        settings.metadata["manually_updated"] = datetime.utcnow().isoformat()
        
        db.commit()
        db.refresh(settings)
        return settings
    
    # ===== MEMORY SUMMARIZATION & MAINTENANCE =====
    def summarize_conversation(self, db: Session, conversation_id: str) -> str:
        """Create a detailed summary of a conversation."""
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at).all()
        
        if not messages:
            return "No messages in this conversation."
        
        # Extract key information
        user_messages = [m for m in messages if m.role == "user"]
        assistant_messages = [m for m in messages if m.role == "assistant"]
        
        # Get conversation metadata
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        duration = None
        if conversation and conversation.started_at and conversation.ended_at:
            duration = (conversation.ended_at - conversation.started_at).total_seconds() / 60
        
        # Create summary
        summary_parts = [
            f"Conversation Summary (ID: {conversation_id[:8]}...):",
            f"- Total messages: {len(messages)} ({len(user_messages)} user, {len(assistant_messages)} assistant)",
        ]
        
        if duration:
            summary_parts.append(f"- Duration: {duration:.1f} minutes")
        
        # Extract topics
        topics = self._extract_topics_from_messages(messages)
        if topics:
            summary_parts.append(f"- Main topics: {', '.join(topics[:5])}")
        
        # Extract key decisions or actions
        action_phrases = ["decided to", "will", "going to", "plan to", "promised"]
        actions = []
        for msg in user_messages:
            content_lower = msg.content.lower()
            for phrase in action_phrases:
                if phrase in content_lower:
                    # Extract the action part
                    start_idx = content_lower.find(phrase)
                    action = msg.content[start_idx:start_idx + 100]
                    actions.append(action.strip())
                    break
        
        if actions:
            summary_parts.append(f"- Key actions/decisions: {len(actions)} noted")
        
        # Sentiment analysis
        sentiments = [m.sentiment for m in messages if m.sentiment]
        if sentiments:
            from collections import Counter
            sentiment_counts = Counter(sentiments)
            dominant_sentiment = sentiment_counts.most_common(1)[0][0] if sentiment_counts else "neutral"
            summary_parts.append(f"- Overall sentiment: {dominant_sentiment}")
        
        return "\n".join(summary_parts)
    
    def _extract_topics_from_messages(self, messages: List[Message]) -> List[str]:
        """Extract topics from messages."""
        topic_categories = {
            "Work/Career": ["work", "job", "career", "office", "colleague", "boss", "project"],
            "Relationships": ["friend", "family", "partner", "relationship", "love", "dating"],
            "Hobbies": ["hobby", "sport", "game", "music", "art", "read", "movie"],
            "Technology": ["computer", "phone", "app", "software", "code", "internet", "ai"],
            "Health": ["health", "doctor", "exercise", "diet", "sleep", "stress"],
            "Education": ["study", "learn", "school", "university", "course", "book"],
            "Travel": ["travel", "vacation", "trip", "hotel", "flight", "destination"]
        }
        
        all_content = " ".join([m.content.lower() for m in messages])
        detected_topics = []
        
        for topic, keywords in topic_categories.items():
            if any(keyword in all_content for keyword in keywords):
                detected_topics.append(topic)
        
        return detected_topics
    
    def cleanup_old_memories(self, db: Session, days_old: int = 90):
        """Clean up old or low-confidence memories."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        # Archive or delete old, low-confidence memories
        old_memories = db.query(LongTermMemory).filter(
            LongTermMemory.updated_at < cutoff_date,
            LongTermMemory.confidence < 0.3,
            LongTermMemory.is_active == True
        ).all()
        
        archived_count = 0
        for memory in old_memories:
            memory.is_active = False
            memory.metadata = memory.metadata or {}
            memory.metadata["archived_at"] = datetime.utcnow().isoformat()
            memory.metadata["archived_reason"] = f"old_low_confidence_{days_old}days"
            archived_count += 1
        
        # Delete expired memories
        expired_memories = db.query(LongTermMemory).filter(
            LongTermMemory.expires_at < datetime.utcnow(),
            LongTermMemory.is_active == True
        ).all()
        
        deleted_count = 0
        for memory in expired_memories:
            db.delete(memory)
            deleted_count += 1
        
        db.commit()
        
        logger.info(f"✅ Memory cleanup: Archived {archived_count}, Deleted {deleted_count} memories")
        return {"archived": archived_count, "deleted": deleted_count}
    
    def get_memory_stats(self, db: Session, user_id: str = None) -> Dict:
        """Get memory statistics."""
        stats = {}
        
        # User-specific stats
        if user_id:
            user_memories = db.query(LongTermMemory).filter(
                LongTermMemory.user_id == user_id,
                LongTermMemory.is_active == True
            )
            
            stats["total_memories"] = user_memories.count()
            stats["by_category"] = db.query(
                LongTermMemory.category,
                db.func.count(LongTermMemory.id)
            ).filter(
                LongTermMemory.user_id == user_id,
                LongTermMemory.is_active == True
            ).group_by(LongTermMemory.category).all()
            
            stats["avg_confidence"] = db.query(
                db.func.avg(LongTermMemory.confidence)
            ).filter(
                LongTermMemory.user_id == user_id,
                LongTermMemory.is_active == True
            ).scalar() or 0
            
        # Global stats
        stats["total_users"] = db.query(User).count()
        stats["total_conversations"] = db.query(Conversation).count()
        stats["total_messages"] = db.query(Message).count()
        
        return stats


# Global memory manager instance
memory_manager = MemoryManager()