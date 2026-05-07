@echo off
setlocal
echo [update] Upgrading lock file...
uv lock --upgrade
if errorlevel 1 exit /b %ERRORLEVEL%

echo [update] Syncing...
uv sync --all-extras
if errorlevel 1 exit /b %ERRORLEVEL%

echo [update] ruff check...
uv run ruff check
if errorlevel 1 exit /b %ERRORLEVEL%

echo [update] ruff format check...
uv run ruff format --check
if errorlevel 1 exit /b %ERRORLEVEL%

echo [update] mypy...
uv run mypy
if errorlevel 1 exit /b %ERRORLEVEL%

echo [update] tests...
call "%~dp0tools\run_tests.bat"
if errorlevel 1 exit /b %ERRORLEVEL%

echo [update] Done.
