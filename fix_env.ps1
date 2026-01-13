# Fix environment variable mismatch
Write-Host "🔧 Fixing environment variable configuration..." -ForegroundColor Cyan

# Backup old .env
if (Test-Path ".env") {
    Copy-Item .env .env.backup -Force
    Write-Host "📋 Backed up .env to .env.backup" -ForegroundColor Yellow
}

# Create corrected .env
Write-Host "Creating corrected .env file..." -ForegroundColor Green
@"
# ===== GROQ API =====
GROQ_API_KEY=YOUR_GROQ_API_KEY_HERE
GROQ_MODEL=llama-3.1-8b-instant
GROQ_TIMEOUT=30

# ===== APP SETTINGS =====
APP_PORT=8007
APP_HOST=0.0.0.0
APP_ENV=development
LOG_LEVEL=INFO

# ===== DATABASE =====
DATABASE_URL=sqlite+aiosqlite:///./empathai.db

# ===== PERSONA SETTINGS =====
PERSONA_NAME=Alex
PERSONA_AGE=28
PERSONA_BACKGROUND=Digital artist from Portland who loves hiking, anime, and photography

# ===== MEMORY SETTINGS =====
SHORT_TERM_MEMORY_SIZE=10
SUMMARY_WINDOW_SIZE=20
MEMORY_RETENTION_DAYS=365
MEMORY_CONFIDENCE_THRESHOLD=0.3
MAX_MEMORIES_PER_USER=1000
MEMORY_CACHE_SIZE=1000

# ===== CONVERSATION SETTINGS =====
MAX_HISTORY_MESSAGES=20
MAX_CONVERSATION_LENGTH=50
CONVERSATION_TIMEOUT_MINUTES=60

# ===== SECURITY =====
CORS_ORIGINS=http://localhost:3000
SECRET_KEY=your-secret-key-change-in-production
"@ | Out-File -FilePath .env -Encoding UTF8

Write-Host "✅ Created new .env file" -ForegroundColor Green

# Test the settings
Write-Host "`n🧪 Testing settings import..." -ForegroundColor Blue
try {
    python -c "
import sys
sys.path.insert(0, '.')
from app.config.settings import settings
print('✅ Settings loaded successfully!')
print(f'  Persona: {settings.PERSONA_NAME}')
print(f'  Port: {settings.APP_PORT}')
print(f'  Database: {settings.DATABASE_URL[:30]}...')
"
} catch {
    Write-Host "❌ Settings test failed: $_" -ForegroundColor Red
}

Write-Host "`n📋 Next steps:" -ForegroundColor Cyan
Write-Host "1. Run: python empathai_groq_v2.py" -ForegroundColor White
Write-Host "2. Or run the simple version: python empathai_simple.py" -ForegroundColor White