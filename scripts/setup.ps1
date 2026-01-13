# EmpathAI Setup Script (PowerShell)
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🚀 EmpathAI Chatbot Setup (PowerShell)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Create directories
Write-Host "Step 1: Creating directories..." -ForegroundColor Blue
$dirs = @("data/faiss_index", "data/backups", "logs", "docker/postgres")
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  Created: $dir" -ForegroundColor Green
    }
}

# Step 2: Setup .env file
Write-Host "`nStep 2: Setting up environment file..." -ForegroundColor Blue
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "  Copied .env.example to .env" -ForegroundColor Green
        Write-Host "  ⚠️  Please edit .env and add your Gemini API key!" -ForegroundColor Yellow
        Write-Host "     GEMINI_API_KEY=your_key_here" -ForegroundColor Yellow
    } else {
        Write-Host "  ❌ .env.example not found" -ForegroundColor Red
    }
} else {
    Write-Host "  ✅ .env file already exists" -ForegroundColor Green
}

# Step 3: Check Docker
Write-Host "`nStep 3: Checking Docker..." -ForegroundColor Blue
try {
    docker --version 2>&1 | Out-Null
    Write-Host "  ✅ Docker is installed" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Docker not found" -ForegroundColor Red
    Write-Host "  Please install Docker Desktop from:" -ForegroundColor Yellow
    Write-Host "  https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    Write-Host "  Then restart Docker and run this script again." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Step 4: Start Docker services
Write-Host "`nStep 4: Starting Docker services..." -ForegroundColor Blue
try {
    Write-Host "  Starting PostgreSQL and Redis..." -ForegroundColor Gray
    docker-compose up -d postgres redis 2>&1 | Out-Null
    
    # Wait for services to start
    Write-Host "  Waiting for services to be ready (10 seconds)..." -ForegroundColor Gray
    Start-Sleep -Seconds 10
    
    Write-Host "  ✅ Docker services started" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️  Could not start Docker services" -ForegroundColor Yellow
    Write-Host "  Trying manual start..." -ForegroundColor Yellow
}

# Step 5: Install Python dependencies
Write-Host "`nStep 5: Installing Python dependencies..." -ForegroundColor Blue
try {
    # Check if requirements.txt exists
    if (Test-Path "requirements.txt") {
        pip install -r requirements.txt
        Write-Host "  ✅ Dependencies installed" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  requirements.txt not found" -ForegroundColor Yellow
        # Create a basic requirements.txt
        @"
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-dotenv==1.0.0
google-generativeai==0.3.2
sentence-transformers==2.2.2
faiss-cpu==1.7.4
psycopg2-binary==2.9.9
redis==5.0.1
pydantic==2.5.0
"@ | Out-File -FilePath "requirements.txt" -Encoding UTF8
        Write-Host "  Created basic requirements.txt" -ForegroundColor Green
        pip install -r requirements.txt
    }
} catch {
    Write-Host "  ⚠️  Could not install dependencies with pip" -ForegroundColor Yellow
    Write-Host "  Trying with python -m pip..." -ForegroundColor Yellow
    python -m pip install -r requirements.txt
}

# Step 6: Create VS Code settings
Write-Host "`nStep 6: Creating VS Code settings..." -ForegroundColor Blue
if (-not (Test-Path ".vscode")) {
    New-Item -ItemType Directory -Path ".vscode" | Out-Null
}

$settingsContent = @'
{
    "python.defaultInterpreterPath": "python",
    "python.testing.pytestEnabled": true,
    "files.exclude": {
        "**/__pycache__": true,
        "**/.pytest_cache": true
    }
}
'@

$settingsContent | Out-File -FilePath ".vscode/settings.json" -Encoding UTF8
Write-Host "  ✅ VS Code settings created" -ForegroundColor Green

# Step 7: Final instructions
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "✅ SETUP COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 NEXT STEPS:" -ForegroundColor Blue
Write-Host ""
Write-Host "1. Edit .env file and add your Gemini API key:" -ForegroundColor Yellow
Write-Host "   Open .env and replace: GEMINI_API_KEY=your_key_here" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Start the application:" -ForegroundColor Green
Write-Host "   docker-compose up app" -ForegroundColor White
Write-Host ""
Write-Host "3. Open in browser:" -ForegroundColor Green
Write-Host "   http://localhost:8000" -ForegroundColor White
Write-Host "   http://localhost:8000/docs (API documentation)" -ForegroundColor White
Write-Host ""
Write-Host "4. Test the API:" -ForegroundColor Green
Write-Host '   curl -X POST http://localhost:8000/api/v1/chat ^' -ForegroundColor White
Write-Host '        -H "Content-Type: application/json" ^' -ForegroundColor White
Write-Host '        -d "{\"user_id\": \"test123\", \"message\": \"Hello!\"}"' -ForegroundColor White
Write-Host ""
Write-Host "💡 TIPS:" -ForegroundColor Blue
Write-Host "• Check if Docker Desktop is running" -ForegroundColor Gray
Write-Host "• Run in Git Bash for better terminal experience" -ForegroundColor Gray
Write-Host "• Use Ctrl+C to stop the application" -ForegroundColor Gray
Write-Host ""