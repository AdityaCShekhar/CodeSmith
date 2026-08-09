@echo off
setlocal
chcp 65001 >nul

set "CODESMITH_DIR=%~dp0"
set "PYTHONUTF8=1"
set "PYTHONPATH=%CODESMITH_DIR%src;%PYTHONPATH%"
if not defined OLLAMA_URL set "OLLAMA_URL=http://localhost:11434"

where py >nul 2>nul
if errorlevel 1 goto use_python
py -3 -m codesmith.batch %*
set "CODESMITH_EXIT=%ERRORLEVEL%"
goto finished

:use_python
python -m codesmith.batch %*
set "CODESMITH_EXIT=%ERRORLEVEL%"

:finished
exit /b %CODESMITH_EXIT%
