@echo off
chcp 65001 >nul
cd /d "%~dp0"
python scripts\poner_resultado.py
echo.
pause
