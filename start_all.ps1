Write-Host "=============================================="
Write-Host "  Starting OmniLocal Pipeline (No Docker)"
Write-Host "=============================================="

# Define environment variables explicitly if .env is missing
$env:WEBHOOK_BASE_URL="http://localhost:8000"
$env:PHASE1_URL="http://localhost:8001"
$env:PHASE2_URL="http://localhost:8002"
$env:PHASE3_URL="http://localhost:8003"
$env:PHASE4_URL="http://localhost:8004"
$env:PHASE5_URL="http://localhost:8005"

# Utility function to start a process in a new window
function Start-ServiceWindow {
    param ($Title, $Command)
    $escapedCommand = "`$Host.UI.RawUI.WindowTitle = '$Title'; $Command"
    Start-Process powershell -WorkingDirectory $PWD -ArgumentList "-NoExit", "-Command", $escapedCommand
}

Write-Host "`nStarting Frontend on port 3000..."
Start-ServiceWindow "Frontend" "cd frontend; npm run dev -- --port 3000"

Write-Host "Starting Orchestrator on port 8000..."
Start-ServiceWindow "Orchestrator" ".\venv\Scripts\Activate.ps1; cd orchestrator; uvicorn app.main:app --port 8000"

Write-Host "Starting Phase Workers (ports 8001-8005)..."
Start-ServiceWindow "Phase 0" ".\venv\Scripts\Activate.ps1; cd phase0; uvicorn app.main:app --port 8010"
Start-ServiceWindow "Phase 1" ".\venv\Scripts\Activate.ps1; cd phase1; uvicorn app.main:app --port 8001"
Start-ServiceWindow "Phase 2" ".\venv\Scripts\Activate.ps1; cd phase2; uvicorn app.main:app --port 8002"
Start-ServiceWindow "Phase 3" ".\venv\Scripts\Activate.ps1; cd phase3; uvicorn app.main:app --port 8003"
Start-ServiceWindow "Phase 4" ".\venv\Scripts\Activate.ps1; cd phase4; uvicorn app.main:app --port 8004"
Start-ServiceWindow "Phase 5" ".\venv\Scripts\Activate.ps1; cd phase5; uvicorn app.main:app --port 8005"

Write-Host "`n=============================================="
Write-Host " All services are spinning up in separate windows!"
Write-Host " Frontend: http://localhost:3000"
Write-Host " Orchestrator API: http://localhost:8000/docs"
Write-Host "=============================================="
