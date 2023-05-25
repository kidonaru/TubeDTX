cd %~dp0

call setup.bat true

call venv\Scripts\activate.bat

python launch.py

deactivate
