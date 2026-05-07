@echo off
setlocal
where uv >nul 2>nul
if errorlevel 1 (
    echo [ERROR] uv is not installed. Install from https://docs.astral.sh/uv/ and re-run.
    exit /b 1
)

echo [install] Syncing dependencies via uv...
uv sync --all-extras
if errorlevel 1 exit /b %ERRORLEVEL%

echo [install] Running unit tests...
call "%~dp0tools\run_tests.bat"
if errorlevel 1 exit /b %ERRORLEVEL%

echo [install] Done.
