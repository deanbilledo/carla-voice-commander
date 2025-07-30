@echo off
echo 🚗 Voice Commander - Webots Edition
echo ====================================
echo Starting overlay interface...
echo.

cd /d "%~dp0"
python test_overlay.py

echo.
echo Application finished.
pause
