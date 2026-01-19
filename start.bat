@echo off
REM Quick Start Script for Windows - File Converter Backend
REM This script helps you start all services quickly

echo ========================================
echo  File Converter Backend - Quick Start
echo ========================================
echo.

echo Choose an option:
echo.
echo 1. Start with Docker (Recommended)
echo 2. Start locally (Redis + Celery + FastAPI)
echo 3. Start Celery worker only
echo 4. Start FastAPI only
echo 5. Check health
echo 6. Open API docs
echo 7. Open Flower dashboard
echo 8. Stop Docker services
echo.

set /p choice="Enter choice (1-8): "

if "%choice%"=="1" goto docker
if "%choice%"=="2" goto local
if "%choice%"=="3" goto worker
if "%choice%"=="4" goto api
if "%choice%"=="5" goto health
if "%choice%"=="6" goto docs
if "%choice%"=="7" goto flower
if "%choice%"=="8" goto stop
goto end

:docker
echo.
echo Starting all services with Docker...
docker-compose up --build
goto end

:local
echo.
echo Starting Redis...
start /B docker run -d -p 6379:6379 --name file-converter-redis redis:7-alpine

timeout /t 3 /nobreak > nul

echo Starting Celery worker...
start /B celery -A app.celery_app worker --loglevel=info --pool=solo

timeout /t 3 /nobreak > nul

echo Starting FastAPI...
python -m uvicorn app.main:app --reload
goto end

:worker
echo.
echo Starting Celery worker...
celery -A app.celery_app worker --loglevel=info --pool=solo
goto end

:api
echo.
echo Starting FastAPI...
python -m uvicorn app.main:app --reload
goto end

:health
echo.
echo Checking health...
curl http://localhost:8000/health
echo.
pause
goto end

:docs
echo.
echo Opening API documentation...
start http://localhost:8000/docs
goto end

:flower
echo.
echo Opening Flower dashboard...
start http://localhost:5555
goto end

:stop
echo.
echo Stopping Docker services...
docker-compose down
goto end

:end
echo.
echo Done!
