@echo off
echo ========================================
echo E M P A T H A I   S E T U P
echo ========================================
echo.

:CHECK_DOCKER
echo Step 1: Checking Docker Desktop...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker not installed!
    echo.
    echo Please install Docker Desktop:
    echo 1. Download from https://www.docker.com/products/docker-desktop/
    echo 2. Run installer
    echo 3. Restart computer
    echo.
    pause
    exit /b 1
)

echo ✅ Docker is installed
echo.

echo Checking if Docker is running...
docker ps >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Desktop is not running
    echo.
    echo Please:
    echo 1. Open Docker Desktop from Start Menu
    echo 2. Wait for it to show "Docker Desktop is running"
    echo 3. Try again
    echo.
    echo Press any key to continue after starting Docker Desktop...
    pause >nul
    goto CHECK_DOCKER
)

echo ✅ Docker Desktop is running
echo.

:SETUP_ENV
echo Step 2: Setting up environment...
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env"
        echo Created .env file
        echo.
        echo ⚠️  IMPORTANT: Edit .env file and add:
        echo     GEMINI_API_KEY=your_actual_key_here
        echo.
    ) else (
        echo Creating .env file...
        echo GEMINI_API_KEY=>.env
        echo DATABASE_URL=postgresql://chatbot:password123@localhost:5432/chatbot_memory>>.env
        echo REDIS_URL=redis://localhost:6379/0>>.env
    )
)

:CREATE_DIRS
echo Step 3: Creating directories...
if not exist "data\faiss_index" mkdir "data\faiss_index"
if not exist "data\backups" mkdir "data\backups"
if not exist "logs" mkdir "logs"
if not exist "docker\postgres" mkdir "docker\postgres"
echo ✅ Directories created
echo.

:START_SERVICES
echo Step 4: Starting PostgreSQL and Redis...
docker-compose up -d postgres redis
echo ⏳ Waiting for services to start...
timeout /t 10 /nobreak >nul
echo ✅ Services started
echo.

:CHECK_SERVICES
echo Step 5: Verifying services...
docker ps --format "table {{.Names}}\t{{.Status}}"
echo.

:PYTHON_SETUP
echo Step 6: Python setup...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found
    echo Install Python 3.11+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Installing dependencies...
pip install -r requirements.txt 2>nul
if %errorlevel% neq 0 (
    echo ⚠️  Trying with --user flag...
    pip install --user -r requirements.txt
)

echo ✅ Python setup complete
echo.

:FINAL
echo ========================================
echo ✅ SETUP COMPLETE!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env file in VS Code
echo 2. Add your Gemini API key
echo 3. Run: docker-compose up app
echo 4. Open: http://localhost:8000
echo.
echo Press any key to open .env file...
pause >nul
notepad .env