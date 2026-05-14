@echo off
cd /d "%~dp0.."
where py >nul 2>nul && py -3 scripts\build_tui.py %* && exit /b %ERRORLEVEL%
python scripts\build_tui.py %*
