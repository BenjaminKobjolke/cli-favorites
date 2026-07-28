@echo off
setlocal
pushd "%~dp0.."
uv run --group dev pyinstaller --name FavPalette --onefile --windowed --noconfirm fav_palette.py
set RC=%ERRORLEVEL%
popd
exit /b %RC%
