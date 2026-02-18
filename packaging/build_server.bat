@echo off
setlocal
set REPO_ROOT=%~dp0..
set OUTPUT_DIR=%REPO_ROOT%\ui\resources\server

if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

cd "%REPO_ROOT%"
poetry run pyinstaller packaging\server.spec ^
    --distpath "%OUTPUT_DIR%" ^
    --workpath %TEMP%\pyinstaller-work ^
    --clean

echo Built: %OUTPUT_DIR%\simtradelab-server.exe
