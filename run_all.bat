@echo off
start "FastAPI_Core" cmd /c "python server.py"
start "Flet_Builder" cmd /c "python start_builder.py"
echo Системы запущены в разных окнах.
pause