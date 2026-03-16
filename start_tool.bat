@echo off
echo Starting Data Product Planning Tool...
echo Setting up Python virtual environment if needed...

if not exist "venv\Scripts\activate.bat" (
    echo Virtual environment not found. Please ensure venv is set up and dependencies are installed.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
echo Starting Streamlit server...
streamlit run app/app.py

pause
