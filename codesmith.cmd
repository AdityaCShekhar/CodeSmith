@echo off
setlocal
chcp 65001 >nul

set "CODESMITH_DIR=%~dp0"
set "CODESMITH_WORK_DIR=%CD%"
set "PYTHONUTF8=1"
set "PYTHONPATH=%CODESMITH_DIR%src;%PYTHONPATH%"
if not defined OLLAMA_URL set "OLLAMA_URL=http://localhost:11434"

if not exist "%CODESMITH_DIR%src\codesmith\__main__.py" (
    echo Error: CodeSmith CLI not found at %CODESMITH_DIR%
    exit /b 1
)

where py >nul 2>nul
if errorlevel 1 goto use_python
py -3 -m codesmith %*
set "CODESMITH_EXIT=%ERRORLEVEL%"
goto finished

:use_python
python -m codesmith %*
set "CODESMITH_EXIT=%ERRORLEVEL%"

:finished
exit /b %CODESMITH_EXIT%
