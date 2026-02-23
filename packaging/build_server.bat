@echo off
setlocal

set REPO_ROOT=%~dp0..
set OUTPUT_DIR=%REPO_ROOT%\ui\resources\server

mkdir "%OUTPUT_DIR%" 2>nul
cd "%REPO_ROOT%"
poetry install --with dev --extras server --quiet
poetry run pyinstaller packaging\server.spec --distpath "%OUTPUT_DIR%" --workpath "%TEMP%\pyinstaller-work" --clean

echo Built: %OUTPUT_DIR%\simtradelab-server.exe
