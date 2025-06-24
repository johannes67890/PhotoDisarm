@echo off
echo Running PhotoDisarm...
echo.

REM Check for Python installation
python --version 2>NUL
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in the PATH.
    echo Please install Python and try again.
    pause
    exit /b 1
)

REM Run the application
python src\launcher.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo An error occurred. Please check the output above.
    pause
)

exit /b
