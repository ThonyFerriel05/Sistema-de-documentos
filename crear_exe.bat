@echo off
REM ============================================================
REM  Arma el programa (.exe) con PyInstaller.
REM  Uso: doble clic en este archivo (dentro de la carpeta del proyecto).
REM  Resultado: dist\SistemaDireccion\SistemaDireccion.exe
REM ============================================================
cd /d "%~dp0"

echo Instalando PyInstaller en el entorno (solo la primera vez tarda)...
uv pip install --python .venv\Scripts\python.exe pyinstaller
if errorlevel 1 goto error

echo Corriendo las pruebas antes de armar el .exe...
.venv\Scripts\python.exe -m unittest pruebas.prueba_sistema
if errorlevel 1 goto error

echo Armando el .exe...
.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean ^
  --onedir --windowed ^
  --name SistemaDireccion ^
  --icon vistas_qt\iconos\sistema.ico ^
  --add-data "vistas_qt\iconos;vistas_qt\iconos" ^
  --add-data "plantillas;plantillas" ^
  --collect-data docx ^
  --exclude-module customtkinter --exclude-module tkinter ^
  main_qt.py
if errorlevel 1 goto error

echo.
echo LISTO: dist\SistemaDireccion\SistemaDireccion.exe
echo Ahora abre instalador.iss con Inno Setup y presiona Compilar (Ctrl+F9).
pause
exit /b 0

:error
echo.
echo ALGO FALLO. Revisa el mensaje de arriba.
pause
exit /b 1
