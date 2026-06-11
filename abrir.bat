@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Abriendo la web del Mundial 2026...
start "" http://127.0.0.1:8765/
python -m http.server 8765
