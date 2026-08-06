@echo off
REM Prune disk + start partial baby build on C: (run before bed)
setlocal
cd /d "%~dp0"
call prune_for_baby_c.bat
call build_baby_c_autofit.bat
