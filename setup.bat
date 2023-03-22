cd %~dp0

python.exe -m venv venv
call venv\Scripts\activate.bat

pip install --upgrade -r requirements.txt

echo "All complate!!! plass any key..."

pause

deactivate
