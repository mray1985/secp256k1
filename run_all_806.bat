@echo off
REM Launch the 806-candidate kangaroo runner fully detached.
REM Uses PowerShell hidden window so it survives CMD/SSH disconnects.
start "" /MIN powershell -WindowStyle Hidden -ExecutionPolicy Bypass -File "%~dp0run_all_806.ps1" -Start 1 -End 806 -HoursPerCandidate 12
echo Runner launched in hidden PowerShell window.
echo Check wgpu_kangaroo_results\runner_log.txt for progress.
