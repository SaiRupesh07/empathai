# start_chatbot.ps1 - Auto-fixes port issues
Write-Host "🚀 Starting EmpathAI Chatbot..." -ForegroundColor Cyan

# Kill existing processes
Write-Host "Cleaning up existing processes..." -ForegroundColor Yellow
taskkill /f /im python.exe 2>nul

# Check available ports
$ports = @(8001, 8002, 8003, 8080, 8081)
$available_port = $null

foreach ($port in $ports) {
    $connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if (-not $connection) {
        $available_port = $port
        break
    }
}

if (-not $available_port) {
    Write-Host "❌ No ports available! Try:" -ForegroundColor Red
    Write-Host "   1. Close other applications" -ForegroundColor Yellow
    Write-Host "   2. Reboot computer" -ForegroundColor Yellow
    exit
}

Write-Host "✅ Using port: $available_port" -ForegroundColor Green

# Create script with dynamic port
$script_content = @"
from fastapi import FastAPI
from pydantic import BaseModel
import google.genai as genai
import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="EmpathAI")

class ChatRequest(BaseModel):
    user_id: str
    message: str

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("❌ Add GEMINI_API_KEY to .env!")
    exit(1)

client = genai.Client(api_key=API_KEY)

@app.get("/")
def root():
    return {"status": "running", "port": $available_port}

@app.post("/chat")
def chat(request: ChatRequest):
    prompt = f"You are Alex, a friendly person.\\n\\nUser: {request.message}\\nAlex:"
    response = client.models.generate_content(model="gemini-2.0-flash-exp", contents=prompt)
    return {"response": response.text, "user_id": request.user_id}

if __name__ == "__main__":
    print(f"🚀 Server: http://localhost:$available_port")
    uvicorn.run(app, host="127.0.0.1", port=$available_port)
"@

$script_content | Out-File -FilePath "temp_chatbot.py" -Encoding UTF8

# Start server
Write-Host "`nStarting server on port $available_port..." -ForegroundColor Green
python temp_chatbot.py