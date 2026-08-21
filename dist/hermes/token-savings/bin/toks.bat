@echo off
rem Portable toks launcher for Windows (companion to the POSIX bin/toks).
rem Resolution order: %TOKS_SKILL_DIR% -> this script's parent dir (skill root).
setlocal
if "%TOKS_SKILL_DIR%"=="" set "TOKS_SKILL_DIR=%~dp0.."
set "PYTHONPATH=%TOKS_SKILL_DIR%\scripts;%PYTHONPATH%"
python -m toks.cli %*
