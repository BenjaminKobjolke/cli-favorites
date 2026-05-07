@echo off
setlocal
set "PROJECT_ROOT=%~dp0"
set "PYTHONPATH=%PROJECT_ROOT%"
set "FAV_TARGET_FILE=%TEMP%\fav_target_%RANDOM%_%RANDOM%.txt"
if exist "%FAV_TARGET_FILE%" del /q "%FAV_TARGET_FILE%"
"%PROJECT_ROOT%.venv\Scripts\python.exe" -m app.cli.fav %*
set "TARGET="
if exist "%FAV_TARGET_FILE%" (
    set /p TARGET=<"%FAV_TARGET_FILE%"
    del /q "%FAV_TARGET_FILE%"
)
endlocal & if not "%TARGET%"=="" cd /d "%TARGET%"
