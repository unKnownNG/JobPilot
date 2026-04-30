@echo off
echo Starting JobPilot...

:: Start the Python Backend in a new window
start "JobPilot Backend" cmd /k "cd backend && echo Starting FastAPI Server... && python -m uvicorn app.main:app --reload --port 8000"

:: Start the Next.js Frontend in a new window
start "JobPilot Frontend" cmd /k "cd frontend && echo Starting Next.js Server... && npm run dev"

echo Both servers are starting up!
echo You can view the app at http://localhost:3000
