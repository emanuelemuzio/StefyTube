if not exist "venv" (python -m venv venv)
call venv\Scripts\activate.bat
pip install -r requirements.txt >nul 2>&1
python app.py 