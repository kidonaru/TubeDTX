cd %~dp0

:: 現在のバージョンがローカルバージョンと違う場合、setupする
IF NOT EXIST .locel_version (
  echo.>.locel_version
)
set /p local_version=<.locel_version
set /p current_version=<VERSION

IF NOT "%local_version%"=="%current_version%" (
  call setup.bat true
)

call venv\Scripts\activate.bat

python launch.py

deactivate
