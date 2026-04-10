Write-Host "=============================================="
Write-Host "  Installing OmniLocal Dependencies"
Write-Host "=============================================="

# 1. Setup Virtual Environment
Write-Host "`n[1/3] Creating and activating Virtual Environment..."
If (-Not (Test-Path "venv")) {
    python -m venv venv
}
.\venv\Scripts\Activate.ps1

# 2. Install Python Dependencies
Write-Host "`n[2/3] Installing Python Dependencies for all services..."
pip install -r orchestrator/requirements.txt
pip install -r phase1/requirements.txt
pip install -r phase2/requirements.txt
pip install -r phase3/requirements.txt
pip install -r phase4/requirements.txt
pip install -r phase5/requirements.txt
pip install -r phase0/requirements.txt

# 3. Install NPM Dependencies
Write-Host "`n[3/3] Installing Frontend Dependencies..."
Set-Location frontend
npm install
Set-Location ..

Write-Host "`n=============================================="
Write-Host "  Setup Complete! You can now run start_all.ps1"
Write-Host "=============================================="
