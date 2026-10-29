@echo off
title Marketing Creative Brief & Ad Variant Generator
echo =========================================================================
echo  Launching Marketing Creative Brief ^& Ad Variant Generator
echo =========================================================================
echo.

set "PYTHON_EXE=C:\Users\viraj\AppData\Local\Programs\Python\Python314\python.exe"

if exist "%PYTHON_EXE%" (
    echo Using Python at: %PYTHON_EXE%
    "%PYTHON_EXE%" -m streamlit run app.py --browser.gatherUsageStats=false
) else (
    echo Using system Python in PATH...
    python -m streamlit run app.py --browser.gatherUsageStats=false
)

if %ERRORLEVEL% neq 0 (
    echo.
    echo Streamlit stopped with error code %ERRORLEVEL%.
)

pause
