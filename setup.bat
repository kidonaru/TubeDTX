cd %~dp0

set skip_key_wait=%1

git submodule update --init --recursive

python.exe -m venv venv
call venv\Scripts\activate.bat

pip install --upgrade -r requirements.txt

cd pytube
pip install -e .
cd ..

pip list

if not "%skip_key_wait%"=="true" (
  echo "All complate!!! plass any key..."
  pause
)

deactivate
