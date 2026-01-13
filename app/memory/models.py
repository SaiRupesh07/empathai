from sqlalchemy import create_engine, Column, String, Integer, Boolean, Float, Text, DateTime, JSON, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

Base = declarative_base()

# ===== ENUMS =====
class MemoryPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class MemoryCategory(enum.Enum):
    PREFERENCE = "preference"
    FACT = "fact"
    EXPERIENCE = "experience"
    GOAL = "goal"
    EMOTION = "emotion"
    RELATIONSHIP = "relationship"
    SKILL = "skill"
    OPINION = "opinion"
    GENERAL = "general"

class ConversationStatus(enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class ToneType(enum.Enum):
    CASUAL = "casual"
    FORMAL = "formal"
    PROFESSIONAL = "professional"
    EMPATHETIC = "empathetic"
    PLAYFUL = "playful"
    SUPPORTIVE = "supportive"

# ===== MODELS =====
class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100))
    email = Column(String(255))
    
    # Tracking
    conversation_count = Column(Integer, default=0)
    total_messages = Column(Integer, default=0)
    avg_sentiment = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_seen = Column(DateTime(timezone=True))
    last_conversation_at = Column(DateTime(timezone=True))
    
    # Metadata
    metadata = Column(JSONB, default=dict)
    preferences = Column(JSONB, default=dict)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    memories = relationship("LongTermMemory", back_populates="user", cascade="all, delete-orphan")
    persona_settings = relationship("PersonaSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, user_id={self.user_id}, conversations={self.conversation_count})>"


class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False, index=True)
    session_id = Column(String(255), index=True)
    
    # Status
    status = Column(Enum(ConversationStatus), default=ConversationStatus.ACTIVE)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True))
    last_message_at = Column(DateTime(timezone=True))
    
    # Analytics
    message_count = Column(Integer, default=0)
    avg_message_length = Column(Float, default=0.0)
    dominant_sentiment = Column(String(20))
    dominant_emotion = Column(String(20))
    topics = Column(ARRAY(String), default=list)
    
    # Content
    title = Column(String(255))
    summary = Column(Text)
    
    # Metadata
    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, user={self.user_id}, messages={self.message_count})>"


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('conversations.id'), nullable=False, index=True)
    sequence_number = Column(Integer)  # Order in conversation
    
    # Content
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    tokens = Column(Integer)
    
    # Analysis
    sentiment = Column(String(20))
    emotion_data = Column(JSONB)  # {"type": "joy", "intensity": 0.8, "categories": [...]}
    topics = Column(ARRAY(String), default=list)
    
    # Embeddings
    embedding = Column(Text)  # JSON string of vector embedding
    embedding_model = Column(String(50))  # Which model was used
    
    # Metadata
    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        return f"<Message(id={self.id}, role={self.role}, length={len(self.content) if self.content else 0})>"


class LongTermMemory(Base):
    __tablename__ = "long_term_memories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False, index=True)
    
    # Content
    memory_type = Column(String(50), nullable=False)  # 'fact', 'preference', 'event', 'summary', 'habit'
    category = Column(Enum(MemoryCategory), default=MemoryCategory.GENERAL)
    content = Column(Text, nullable=False)
    memory_hash = Column(String(64), unique=True, index=True)  # For deduplication
    
    # Quality metrics
    confidence = Column(Float, default=1.0)
    importance = Column(Float, default=0.5)
    priority = Column(Enum(MemoryPriority), default=MemoryPriority.MEDIUM)
    relevance_score = Column(Float, default=0.0)
    
    # Embeddings
    embedding = Column(Text)  # JSON string of vector embedding
    embedding_model = Column(String(50))
    
    # Source tracking
    source_conversation = Column(UUID(as_uuid=True))
    source_message = Column(UUID(as_uuid=True))
    extraction_method = Column(String(50))  # 'auto', 'manual', 'inferred'
    
    # Access tracking
    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime(timezone=True))
    first_accessed = Column(DateTime(timezone=True))
    
    # Lifecycle
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verification_count = Column(Integer, default=0)
    
    # Expiration
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True))
    archived_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="memories")
    
    # Metadata
    metadata = Column(JSONB, default=dict)
    
    def __repr__(self):
        return f"<LongTermMemory(id={self.id}, type={self.memory_type}, category={self.category}, confidence={self.confidence})>"


class PersonaSettings(Base):
    __tablename__ = "persona_settings"
    
    user_id = Column(String(255), ForeignKey('users.user_id'), primary_key=True)
    
    # Communication style
    preferred_tone = Column(Enum(ToneType), default=ToneType.CASUAL)
    communication_style = Column(String(50), default='balanced')  # 'concise', 'detailed', 'storytelling'
    formality_level = Column(Integer, default=3)  # 1-5 scale
    
    # Interests & Preferences
    topics_of_interest = Column(ARRAY(String), default=list)
    dislikes = Column(ARRAY(String), default=list)
    conversation_topics = Column(JSONB, default=dict)  # {"technology": 0.8, "art": 0.6}
    
    # Personality traits (1-10 scale)
    friendliness = Column(Integer, default=7)
    curiosity = Column(Integer, default=6)
    humor_level = Column(Integer, default=5)
    empathy_level = Column(Integer, default=8)
    assertiveness = Column(Integer, default=5)
    
    # Learning & Interaction
    trust_level = Column(Integer, default=50)  # 0-100
    learning_speed = Column(String(20), default='medium')  # 'slow', 'medium', 'fast'
    memory_retention = Column(Float, default=0.7)  # 0-1
    
    # Behavioral preferences
    preferred_response_length = Column(String(20), default='medium')  # 'short', 'medium', 'long'
    ask_questions_frequency = Column(Float, default=0.3)  # 0-1
    share_personal_stories = Column(Boolean, default=True)
    
    # Safety & Boundaries
    boundaries = Column(JSONB, default=dict)
    sensitive_topics = Column(ARRAY(String), default=list)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_adjusted = Column(DateTime(timezone=True))
    
    # Metadata
    metadata = Column(JSONB, default=dict)
    adjustment_history = Column(JSONB, default=list)
    
    # Relationships
    user = relationship("User", back_populates="persona_settings")
    
    def __repr__(self):
        return f"<PersonaSettings(user={self.user_id}, tone={self.preferred_tone}, trust={self.trust_level})>"


class MemoryInteraction(Base):
    __tablename__ = "memory_interactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    memory_id = Column(UUID(as_uuid=True), ForeignKey('long_term_memories.id'), nullable=False)
    user_id = Column(String(255), nullable=False, index=True)
    
    # Interaction type
    interaction_type = Column(String(50))  # 'recall', 'reference', 'update', 'verify', 'contradict'
    
    # Context
    conversation_id = Column(UUID(as_uuid=True))
    message_id = Column(UUID(as_uuid=True))
    context = Column(Text)
    
    # Outcome
    was_relevant = Column(Boolean)
    relevance_score = Column(Float)
    user_feedback = Column(String(50))  # 'correct', 'incorrect', 'partial', 'irrelevant'
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Metadata
    metadata = Column(JSONB, default=dict)
    
    # Relationships
    memory = relationship("LongTermMemory")
    
    def __repr__(self):
        return f"<MemoryInteraction(memory={self.memory_id}, type={self.interaction_type}, relevant={self.was_relevant})>"


class ConversationSummary(Base):
    __tablename__ = "conversation_summaries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('conversations.id'), unique=True, nullable=False)
    user_id = Column(String(255), nullable=False, index=True)
    
    # Summary content
    summary_text = Column(Text, nullable=False)
    key_points = Column(ARRAY(String), default=list)
    decisions_made = Column(ARRAY(String), default=list)
    actions_planned = Column(ARRAY(String), default=list)
    
    # Analysis
    sentiment_analysis = Column(JSONB)  # {"overall": "positive", "breakdown": {...}}
    emotion_timeline = Column(JSONB)
    topic_distribution = Column(JSONB)
    
    # Quality metrics
    confidence = Column(Float, default=1.0)
    completeness = Column(Float, default=0.0)  # 0-1
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Metadata
    metadata = Column(JSONB, default=dict)
    
    # Relationships
    conversation = relationship("Conversation")
    
    def __repr__(self):
        return f"<ConversationSummary(conversation={self.conversation_id}, key_points={len(self.key_points)})>"


class UserAnalytics(Base):
    __tablename__ = "user_analytics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), unique=True, nullable=False, index=True)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Usage metrics
    messages_today = Column(Integer, default=0)
    conversations_today = Column(Integer, default=0)
    total_messages = Column(Integer, default=0)
    total_conversations = Column(Integer, default=0)
    
    # Engagement metrics
    avg_session_length = Column(Float, default=0.0)
    avg_messages_per_session = Column(Float, default=0.0)
    return_rate = Column(Float, default=0.0)  # Percentage of days user returns
    
    # Content metrics
    preferred_topics = Column(JSONB, default=dict)
    emotion_distribution = Column(JSONB, default=dict)
    sentiment_trend = Column(JSONB, default=dict)
    
    # Memory metrics
    memory_count = Column(Integer, default=0)
    memory_recall_rate = Column(Float, default=0.0)
    memory_accuracy = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Metadata
    metadata = Column(JSONB, default=dict)
    
    def __repr__(self):
        return f"<UserAnalytics(user={self.user_id}, date={self.date.date()}, messages={self.messages_today})>"


# ===== INDEXES ===== (Additional indexes for performance)
# Note: These are conceptual. In practice, create them via migrations.

# Indexes for common queries:
# CREATE INDEX idx_memories_user_category ON long_term_memories(user_id, category);
# CREATE INDEX idx_memories_confidence ON long_term_memories(confidence DESC);
# CREATE INDEX idx_messages_conversation_seq ON messages(conversation_id, sequence_number);
# CREATE INDEX idx_conversations_user_status ON conversations(user_id, status);
# CREATE INDEX idx_memory_interactions_user_memory ON memory_interactions(user_id, memory_id);

# ===== HELPER FUNCTIONS =====
def create_tables(engine):
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")

def drop_tables(engine):
    """Drop all tables in the database."""
    Base.metadata.drop_all(bind=engine)
    print("⚠️ Database tables dropped.")

# ===== INITIALIZATION =====
if __name__ == "__main__":
    # Example usage
    from sqlalchemy import create_engine
    
    DATABASE_URL = "postgresql://username:password@localhost/empathai"
    engine = create_engine(DATABASE_URL)
    
    # Create tables
    create_tables(engine)
    
    print("\n📊 Database Schema Created:")
    for table in Base.metadata.tables.values():
        print(f"  - {table.name}: {len(table.columns)} columns")