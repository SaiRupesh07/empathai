import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Create SQLite engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite specific
    echo=settings.DEBUG,  # Show SQL queries in debug mode
    pool_pre_ping=True
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
    """Initialize database tables and default data."""
    from app.memory.models import Base as MemoryBase
    
    try:
        # Create all tables
        MemoryBase.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully!")
        
        # Initialize default system persona
        db = SessionLocal()
        try:
            from app.memory.models import PersonaSettings
            
            # Check if default persona exists
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
                    sensitive_topics=["politics", "religion"],
                    metadata={
                        "created_at": "system",
                        "description": "Default empathetic persona"
                    }
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