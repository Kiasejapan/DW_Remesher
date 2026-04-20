@echo off
cd /d "%~dp0"

echo ==============================
echo   BUILD
echo ==============================
cd _build
python build.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ==============================
    echo   BUILD FAILED
    echo ==============================
    pause
    exit /b 1
)
cd ..

echo.
echo ==============================
echo   GIT PUSH
echo ==============================
git add -A
git status --short
echo.

set /p MSG="Commit message (Enter=auto): "
if "%MSG%"=="" set MSG=Update %date% %time:~0,5%

git commit -m "%MSG%"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo No changes to commit.
    pause
    exit /b 0
)

git push origin main
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ==============================
    echo   BUILD + PUSH OK
    echo ==============================
) else (
    echo.
    echo ==============================
    echo   PUSH FAILED
    echo   Check git credentials.
    echo ==============================
)
pause
