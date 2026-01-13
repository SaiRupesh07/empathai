import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # ===== Groq API =====
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    GROQ_TIMEOUT: int = int(os.getenv("GROQ_TIMEOUT", "30"))
    
    # ===== Database =====
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./data/empathai.db"
    )
    
    # ===== Embeddings =====
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", "384"))
    
    # ===== Memory Settings =====
    MEMORY_RETENTION_DAYS: int = int(os.getenv("MEMORY_RETENTION_DAYS", "365"))
    MEMORY_CONFIDENCE_THRESHOLD: float = float(os.getenv("MEMORY_CONFIDENCE_THRESHOLD", "0.3"))
    MAX_MEMORIES_PER_USER: int = int(os.getenv("MAX_MEMORIES_PER_USER", "1000"))
    MEMORY_CACHE_SIZE: int = int(os.getenv("MEMORY_CACHE_SIZE", "1000"))
    
    # ===== Conversation Settings =====
    MAX_HISTORY_MESSAGES: int = int(os.getenv("MAX_HISTORY_MESSAGES", "20"))
    MAX_CONVERSATION_LENGTH: int = int(os.getenv("MAX_CONVERSATION_LENGTH", "50"))
    CONVERSATION_TIMEOUT_MINUTES: int = int(os.getenv("CONVERSATION_TIMEOUT_MINUTES", "60"))
    
    # ===== Persona Settings =====
    DEFAULT_PERSONA_NAME: str = os.getenv("PERSONA_NAME", "Alex")
    DEFAULT_PERSONA_AGE: int = int(os.getenv("PERSONA_AGE", "28"))
    DEFAULT_PERSONA_BACKGROUND: str = os.getenv(
        "PERSONA_BACKGROUND", 
        "digital artist from Portland who loves hiking, anime, and photography"
    )
    
    # ===== API Settings =====
    API_PORT: int = int(os.getenv("APP_PORT", "8007"))
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    DEBUG: bool = os.getenv("APP_ENV", "development") == "development"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # ===== Security =====
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    
    # ===== File Paths =====
    DATA_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    LOGS_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()

# Validate critical settings
def validate_settings():
    """Validate critical settings on startup."""
    if not settings.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is required in environment variables")
    
    if not settings.GROQ_API_KEY.startswith("YOUR_GROQ_API_KEY_HERE"):
        print("⚠️  Warning: GROQ_API_KEY format may be invalid")
    
    # Create data directories
    os.makedirs(settings.DATA_DIR, exist_ok=True)
    os.makedirs(settings.LOGS_DIR, exist_ok=True)
    
    print(f"✅ Settings loaded: {settings.DEFAULT_PERSONA_NAME} on port {settings.API_PORT}")
    return True

# Validate on import
try:
    validate_settings()
except Exception as e:
    print(f"❌ Settings validation failed: {e}")
    raise