@echo off
setlocal
set "PROJECT_ROOT=%~dp0"
set "PYTHONPATH=%PROJECT_ROOT%"
set "PYTHONSAFEPATH=1"
"%PROJECT_ROOT%.venv\Scripts\python.exe" -m app.cli.install_global %*
exit /b %ERRORLEVEL%
