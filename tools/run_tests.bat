@echo off
setlocal
pushd "%~dp0.."
uv run pytest tests -v --ignore=tests/integration
set RC=%ERRORLEVEL%
popd
exit /b %RC%
