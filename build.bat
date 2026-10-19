@echo off
rem Baut die App nach dist\3D-Cost-Manager\ (Ordner-Version, startet schneller als eine Einzel-EXE)
python -m PyInstaller --noconfirm --clean --onedir --windowed ^
  --name "3D-Cost-Manager" ^
  --icon icon.ico ^
  --add-data "icon.ico;." ^
  --collect-data customtkinter ^
  app.py
