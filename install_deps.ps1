# install_deps.ps1
Write-Host "Installing EmpathAI dependencies..." -ForegroundColor Cyan

$packages = @(
    "fastapi==0.104.1",
    "uvicorn[standard]==0.24.0",
    "sqlalchemy==2.0.23",
    "psycopg2-binary==2.9.9",
    "sentence-transformers==2.2.2",
    "faiss-cpu==1.7.4",
    "numpy==1.24.3",
    "google-genai==0.3.0",
    "pydantic==2.5.0",
    "pydantic-settings==2.1.0",
    "python-dotenv==1.0.0",
    "redis==5.0.1"
)

foreach ($package in $packages) {
    Write-Host "Installing $package..." -ForegroundColor Yellow
    pip install $package
}

Write-Host "✅ All dependencies installed!" -ForegroundColor Green