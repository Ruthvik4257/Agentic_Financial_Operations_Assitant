@echo off
echo ==============================================================================
echo  Starting Agentic Financial Operations Assistant (FinOps AI)
echo ==============================================================================

echo [1/3] Activating Python Virtual Environment...
if not exist ".venv" (
    echo Creating .venv...
    python -m venv .venv
    call .venv\Scripts\activate
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate
)

echo [2/3] Starting FastAPI Backend on http://localhost:8000 ...
start cmd /k ".venv\Scripts\uvicorn.exe backend.app.main:app --host 0.0.0.0 --port 8000 --reload"

echo [3/3] Starting React Executive Hub on http://localhost:3000 ...
cd frontend
if not exist "node_modules" (
    npm install
)
start cmd /k "npm run dev"

echo.
echo ==============================================================================
echo  FinOps AI Stack Running!
echo  • React Dashboard: http://localhost:3000
echo  • FastAPI Docs:    http://localhost:8000/docs
echo  • Telegram Bot:    Active in background polling
echo ==============================================================================
