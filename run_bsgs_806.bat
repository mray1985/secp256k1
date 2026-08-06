@echo off
REM Launch BSGS runner for all 806 candidates.
REM Uses -k 512 -S to load existing 7GB bloom files from WORKDIR.
REM Keyhunt cds to WORKDIR automatically (Z:\...\MinGW).
REM Defaults: -k 512 -KFactor auto (from NUMBER_OF_PROCESSORS)
echo [BSGS] Starting 806-candidate runner...
echo [BSGS] Keyhunt: 512  Bloom: load from Z:\
echo.
REM Hidden detached window:
start "" /MIN powershell -WindowStyle Hidden -ExecutionPolicy Bypass ^
  -File "%~dp0run_bsgs_806.ps1" -Start 1 -End 806 -KFactor 512
echo.
echo Runner launched in hidden PowerShell.
echo Progress: %~dp0bsgs_results\runner_log.txt
