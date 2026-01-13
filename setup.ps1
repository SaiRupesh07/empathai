# EmpathAI Setup Script for Windows
Write-Host "🚀 Setting up EmpathAI with Memory System..." -ForegroundColor Cyan

# Check Python version
$pythonVersion = python --version
Write-Host "Python: $pythonVersion"

# Create directory structure
Write-Host "`n📁 Creating directory structure..." -ForegroundColor Yellow
$directories = @(
    "app/database",
    "app/memory", 
    "app/prompt",
    "app/config",
    "app/monitoring",
    "app/models",
    "data",
    "logs",
    "tests"
)

foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force
        Write-Host "  Created: $dir" -ForegroundColor Green
    }
}

# Create __init__.py files
Write-Host "`n📄 Creating module files..." -ForegroundColor Yellow
$initFiles = @(
    "app/__init__.py",
    "app/database/__init__.py", 
    "app/memory/__init__.py",
    "app/prompt/__init__.py",
    "app/config/__init__.py",
    "app/monitoring/__init__.py"
)

foreach ($file in $initFiles) {
    if (!(Test-Path $file)) {
    New-Item -ItemType File -Path $file -Force
    Write-Host "  Created: $file" -ForegroundColor Green
}
}

# Check .env file
Write-Host "`n🔧 Checking configuration..." -ForegroundColor Yellow
if (!(Test-Path ".env")) {
    Write-Host "❌ .env file not found!" -ForegroundColor Red
    Write-Host "Please create a .env file with:" -ForegroundColor White
    Write-Host "GROQ_API_KEY=your_groq_api_key_here" -ForegroundColor White
    Write-Host "GROQ_MODEL=llama-3.1-8b-instant" -ForegroundColor White
    Write-Host "APP_PORT=8007" -ForegroundColor White
    exit 1
} else {
    Write-Host "✅ .env file found" -ForegroundColor Green
}

# Install requirements
Write-Host "`n📦 Installing dependencies..." -ForegroundColor Magenta
try {
    pip install --upgrade pip
    pip install fastapi uvicorn python-dotenv pydantic sqlalchemy aiosqlite groq requests
    
    # Try to install sentence-transformers (optional)
    try {
        pip install sentence-transformers numpy
        Write-Host "✅ AI/ML dependencies installed" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Could not install sentence-transformers, using simple mode" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "❌ Failed to install dependencies: $_" -ForegroundColor Red
    exit 1
}

# Create test script
Write-Host "`n🧪 Creating test script..." -ForegroundColor Blue
$testScript = @'
import requests
import json

print("🧪 Testing EmpathAI API...")

# Test root endpoint
try:
    response = requests.get("http://localhost:8007/", timeout=5)
    print(f"✅ Root endpoint: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"❌ Root endpoint failed: {e}")

# Test health endpoint
try:
    response = requests.get("http://localhost:8007/health", timeout=5)
    print(f"✅ Health endpoint: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"❌ Health endpoint failed: {e}")

# Test chat endpoint
try:
    payload = {
        "user_id": "test_user_001",
        "message": "Hello! My name is Alex and I love programming."
    }
    response = requests.post("http://localhost:8007/chat", 
                           json=payload, 
                           timeout=10)
    print(f"✅ Chat endpoint: {response.status_code}")
    result = response.json()
    print(f"Response: {result['response'][:100]}...")
    print(f"Memories used: {result['memories_used']}")
    print(f"Emotion: {result['emotion_detected']}")
except Exception as e:
    print(f"❌ Chat endpoint failed: {e}")

print("`n✅ Test completed!")
'@

$testScript | Out-File -FilePath "test_api.py" -Encoding UTF8
Write-Host "  Created: test_api.py" -ForegroundColor Green

Write-Host "`n🎉 Setup complete!" -ForegroundColor Green
Write-Host "`n📋 Next steps:" -ForegroundColor Cyan
Write-Host "1. Make sure your .env file has GROQ_API_KEY" -ForegroundColor White
Write-Host "2. Run: python empathai_groq_v2.py" -ForegroundColor White
Write-Host "3. In another terminal, run: python test_api.py" -ForegroundColor White
Write-Host "4. Access docs at: http://localhost:8007/docs" -ForegroundColor White
Write-Host "`n💡 Tip: Check logs/empathai.log for detailed logs" -ForegroundColor Yellow