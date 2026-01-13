import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

# Get database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:password@localhost:5432/empathai"
)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False  # Set to True for SQL logging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

@contextmanager
def get_db():
    """Database session context manager."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        db.close()

def init_database():
    """Initialize database tables."""
    from app.memory.models import Base as MemoryBase
    
    try:
        # Create all tables
        MemoryBase.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully!")
        
        # Create default system persona
        db = SessionLocal()
        try:
            from app.memory.models import PersonaSettings
            
            default_persona = db.query(PersonaSettings).filter(
                PersonaSettings.user_id == "system_default"
            ).first()
            
            if not default_persona:
                default_persona = PersonaSettings(
                    user_id="system_default",
                    preferred_tone="empathetic",
                    communication_style="balanced",
                    topics_of_interest=["technology", "art", "nature", "music", "philosophy"],
                    dislikes=["conflict", "insensitivity", "spam"],
                    trust_level=100,
                    friendliness=9,
                    curiosity=8,
                    empathy_level=9,
                    humor_level=6,
                    assertiveness=5,
                    preferred_response_length="medium",
                    ask_questions_frequency=0.4,
                    share_personal_stories=True,
                    boundaries={"privacy": "high", "personal_info": "medium"},
                    sensitive_topics=["politics", "religion"]
                )
                db.add(default_persona)
                db.commit()
                logger.info("✅ Created default system persona")
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

def health_check():
    """Check database connectivity."""
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

# For FastAPI dependency injection
def get_db_session():
    """FastAPI dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()