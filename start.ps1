Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "   Starting SilentSOS (Levels 1-9)       " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Copy .env.example on first run so JWT_SECRET, AUTH_REQUIRED, SEED_ADMIN_*
# and the AI/stream knobs exist. Generate a real JWT_SECRET before anything
# shared: python -c "import secrets; print(secrets.token_urlsafe(48))"
if (-not (Test-Path ".env")) {
  Copy-Item ".env.example" ".env"
  Write-Host "[0] Created .env from .env.example — set SEED_ADMIN_EMAIL/PASSWORD for first login." -ForegroundColor Yellow
}

Write-Host "`n[1] Starting FastAPI Backend & AI Vision Engine..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; .\venv\Scripts\Activate.ps1; uvicorn main:app --reload --port 8000"

Write-Host "[2] Starting React Dashboard..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host "`nAll systems launching in separate windows!" -ForegroundColor Green
Write-Host "Dashboard: http://localhost:5173" -ForegroundColor White
Write-Host "API Docs:  http://localhost:8000/docs" -ForegroundColor White
Write-Host "Login with the SEED_ADMIN_* account from .env (AUTH_REQUIRED=true by default).`n" -ForegroundColor White
