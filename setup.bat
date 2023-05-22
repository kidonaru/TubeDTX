cd %~dp0

set skip_key_wait=%1

python.exe -m venv venv
call venv\Scripts\activate.bat

pip install --upgrade -r requirements.txt

if not exist pytube (
  git clone https://github.com/kidonaru/pytube.git
)

cd pytube
git checkout v15.0.0-fix
pip install -e .
cd ..

pip list

if not "%skip_key_wait%"=="true" (
  echo "All complate!!! plass any key..."
  pause
)

deactivate
