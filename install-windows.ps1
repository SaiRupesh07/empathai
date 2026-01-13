# EmpathAI Windows Installation Script
Write-Host "🚀 Installing EmpathAI on Windows..." -ForegroundColor Cyan

# Check Python version
$pythonVersion = python --version
Write-Host "Python version: $pythonVersion"

# Upgrade pip
Write-Host "`n📦 Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install build tools
Write-Host "`n🔧 Installing build tools..." -ForegroundColor Yellow
pip install wheel setuptools

# Install base requirements
Write-Host "`n📥 Installing core dependencies..." -ForegroundColor Green
pip install -r requirements-base.txt

# Windows-specific installations
Write-Host "`n🪟 Installing Windows-specific packages..." -ForegroundColor Green

# Install psycopg (PostgreSQL driver)
pip install psycopg==3.1.17

# Install PyTorch for Windows (CPU version)
Write-Host "`n🧠 Installing PyTorch (CPU) for Windows..." -ForegroundColor Magenta
pip install torch --index-url https://download.pytorch.org/whl/cpu

# Install AI/ML packages
Write-Host "`n🤖 Installing AI/ML dependencies..." -ForegroundColor Magenta
pip install sentence-transformers==2.2.2
pip install numpy==1.26.3
pip install scikit-learn==1.4.0

# Install monitoring
Write-Host "`n📊 Installing monitoring tools..." -ForegroundColor Blue
pip install psutil==5.9.7
pip install prometheus-client==0.19.0

Write-Host "`n✅ Installation complete!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Set up your .env file with GROQ_API_KEY" -ForegroundColor White
Write-Host "2. Run: python empathai_groq.py" -ForegroundColor White
Write-Host "3. Access at: http://localhost:8007" -ForegroundColor White