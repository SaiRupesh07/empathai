import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Simple settings class without Pydantic complications."""
    
    def __init__(self):
        # ===== Groq API =====
        self.GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
        self.GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        self.GROQ_TIMEOUT = int(os.getenv("GROQ_TIMEOUT", "30"))
        
        # ===== Database =====
        self.DATABASE_URL = os.getenv(
            "DATABASE_URL", 
            "sqlite+aiosqlite:///./empathai.db"
        )
        
        # ===== App Settings =====
        self.API_PORT = int(os.getenv("APP_PORT", "8007"))
        self.API_HOST = os.getenv("API_HOST", "0.0.0.0")
        self.DEBUG = os.getenv("APP_ENV", "development") == "development"
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        
        # ===== Persona Settings =====
        self.DEFAULT_PERSONA_NAME = os.getenv("PERSONA_NAME", "Alex")
        self.DEFAULT_PERSONA_AGE = int(os.getenv("PERSONA_AGE", "28"))
        self.DEFAULT_PERSONA_BACKGROUND = os.getenv(
            "PERSONA_BACKGROUND", 
            "digital artist from Portland who loves hiking, anime, and photography"
        )
        
        # ===== Memory Settings =====
        self.SHORT_TERM_MEMORY_SIZE = int(os.getenv("SHORT_TERM_MEMORY_SIZE", "10"))
        self.SUMMARY_WINDOW_SIZE = int(os.getenv("SUMMARY_WINDOW_SIZE", "20"))
        
        # ===== Directories =====
        self.DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        self.LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
        
        # Create directories
        os.makedirs(self.DATA_DIR, exist_ok=True)
        os.makedirs(self.LOGS_DIR, exist_ok=True)
        
        # Validate
        self._validate()
    
    def _validate(self):
        """Validate critical settings."""
        if not self.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is required in environment variables")
        
        if not self.GROQ_API_KEY.startswith("YOUR_GROQ_API_KEY_HERE"):
            print("⚠️  Warning: GROQ_API_KEY format may be invalid")
        
        print(f"✅ Settings loaded: {self.DEFAULT_PERSONA_NAME} on port {self.API_PORT}")

# Create global instance
settings = Settings()
