@echo off

REM Check if the requirements.txt file exists
if exist requirements.txt (
    REM Install dependencies using pip
    pip install -r requirements.txt
    if %errorlevel% equ 0 (
        echo OK: All requirements have been successfully installed.
    ) else (
        echo Error: Failed to install requirements !!!
    )
) else (
    echo Error: requirements.txt file not found !!!
)