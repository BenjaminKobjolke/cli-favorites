@echo off
setlocal
pushd "%~dp0.."
uv run pytest tests/integration -v
set RC=%ERRORLEVEL%
popd
exit /b %RC%
