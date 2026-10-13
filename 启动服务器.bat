@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Lumina Commons - local server (KEEP THIS WINDOW OPEN)

echo ============================================================
echo   Lumina Commons  -  local preview server
echo ============================================================
echo.

if not exist "serve.py" goto noserve
if not exist "index.html" goto noindex

set PY=
rem ---- 1) known paths on this machine (kept as-is) ----
if exist "D:\SoftWare\python\python.exe" set PY=D:\SoftWare\python\python.exe
if not defined PY if exist "%USERPROFILE%\.workbuddy\binaries\python\versions\3.13.12\python.exe" set PY=%USERPROFILE%\.workbuddy\binaries\python\versions\3.13.12\python.exe
if not defined PY if exist "D:\Users\pmeoyx\miniconda3\python.exe" set PY=D:\Users\pmeoyx\miniconda3\python.exe

rem ---- 2) common install locations (so it also works on another PC) ----
if not defined PY if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" set PY=%LOCALAPPDATA%\Programs\Python\Python313\python.exe
if not defined PY if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe
if not defined PY if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set PY=%LOCALAPPDATA%\Programs\Python\Python311\python.exe
if not defined PY if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" set PY=%LOCALAPPDATA%\Programs\Python\Python310\python.exe
if not defined PY if exist "%ProgramFiles%\Python313\python.exe" set PY=%ProgramFiles%\Python313\python.exe
if not defined PY if exist "%ProgramFiles%\Python312\python.exe" set PY=%ProgramFiles%\Python312\python.exe
if not defined PY if exist "%ProgramFiles%\Python311\python.exe" set PY=%ProgramFiles%\Python311\python.exe
if not defined PY if exist "%ProgramFiles%\Python310\python.exe" set PY=%ProgramFiles%\Python310\python.exe
if not defined PY if exist "%USERPROFILE%\anaconda3\python.exe" set PY=%USERPROFILE%\anaconda3\python.exe
if not defined PY if exist "%USERPROFILE%\miniconda3\python.exe" set PY=%USERPROFILE%\miniconda3\python.exe

rem ---- 3) last resort: py launcher / python on PATH (really run it, to skip the MS Store stub) ----
if not defined PY py -3 -c "import sys" >nul 2>nul
if not defined PY if not errorlevel 1 set PY=py
if not defined PY python -c "import sys" >nul 2>nul
if not defined PY if not errorlevel 1 set PY=python

if not defined PY goto nopython

echo   Python : %PY%
echo   Folder : %CD%
echo.
echo   Starting server ...  browser opens automatically in a moment.
echo   [!] KEEP THIS WINDOW OPEN.  Closing it stops the server.
echo.

"%PY%" serve.py
set RC=%ERRORLEVEL%

echo.
echo ============================================================
echo   Server stopped  (exit code %RC%).
echo.
echo   If you did NOT close it on purpose, send me the lines
echo   above together with the file  server.log  in this folder.
echo ============================================================
echo.
pause
exit /b 0

:noserve
echo [X] serve.py NOT found in this folder:
echo     %CD%
echo     Keep this .bat together with serve.py.
echo.
pause
exit /b 1

:noindex
echo [X] index.html NOT found in this folder:
echo     %CD%
echo     Please run this .bat from the project folder.
echo.
pause
exit /b 1

:nopython
echo [X] No usable Python found on this machine.
echo     Install Python 3 and tick "Add Python to PATH", then run again.
echo     Download: https://www.python.org/downloads/windows/
echo.
pause
exit /b 1
