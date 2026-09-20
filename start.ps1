Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "   Starting SilentSOS (Levels 1-3)       " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

Write-Host "`n[1] Starting FastAPI Backend & AI Vision Engine..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; .\venv\Scripts\Activate.ps1; uvicorn main:app --reload --port 8000"

Write-Host "[2] Starting React Dashboard..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host "`nAll systems launching in separate windows!" -ForegroundColor Green
Write-Host "👉 Dashboard: http://localhost:5173" -ForegroundColor White
Write-Host "👉 API Docs:  http://localhost:8000/docs`n" -ForegroundColor White
