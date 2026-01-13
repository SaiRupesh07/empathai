# install_packages.ps1
Write-Host "📦 Installing required packages..." -ForegroundColor Cyan

# Activate virtual environment
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

Write-Host "Activating virtual environment..." -ForegroundColor Yellow
.venv\Scripts\Activate.ps1

# Install packages
$packages = @(
    "fastapi==0.104.1",
    "uvicorn[standard]==0.24.0", 
    "google-genai==0.3.0",
    "python-dotenv==1.0.0",
    "pydantic==2.5.0",
    "requests==2.31.0"
)

foreach ($package in $packages) {
    Write-Host "Installing $package..." -ForegroundColor Gray
    pip install $package
}

Write-Host "`n✅ All packages installed!" -ForegroundColor Green
Write-Host "Run: python empathai_simple.py" -ForegroundColor Cyan