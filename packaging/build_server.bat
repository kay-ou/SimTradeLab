@echo off
setlocal

:: 检查 poetry 是否在 PATH 中，不在则尝试常见安装位置
where poetry >nul 2>&1
if %ERRORLEVEL% neq 0 (
    if exist "%APPDATA%\Python\Scripts\poetry.exe" (
        set "PATH=%APPDATA%\Python\Scripts;%PATH%"
    ) else if exist "%USERPROFILE%\.local\bin\poetry.exe" (
        set "PATH=%USERPROFILE%\.local\bin;%PATH%"
    ) else (
        echo 错误: 未找到 poetry，请先安装: https://python-poetry.org
        exit /b 1
    )
)

set REPO_ROOT=%~dp0..
set OUTPUT_DIR=%REPO_ROOT%\ui\resources\server

if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

cd "%REPO_ROOT%"
poetry install --with dev --quiet
poetry run pyinstaller packaging\server.spec ^
    --distpath "%OUTPUT_DIR%" ^
    --workpath %TEMP%\pyinstaller-work ^
    --clean

echo Built: %OUTPUT_DIR%\simtradelab-server.exe
