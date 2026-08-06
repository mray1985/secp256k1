@echo off
setlocal
call "%~dp0paths.bat"
set "SRC=%WORKDIR%"
set "DST=%~dp0bloom_archive"
if not exist "%DST%" mkdir "%DST%"
echo Moving KeyHunt bloom/tables to bloom_archive ^(frees ~7.5 GB on Z:/C:^)
echo   FROM %SRC%
echo   TO   %DST%
echo.
move /Y "%SRC%\keyhunt_bsgs_*.blm" "%DST%\" 2>nul
move /Y "%SRC%\keyhunt_bsgs_*.tbl" "%DST%\" 2>nul
dir "%DST%\keyhunt_bsgs_*" 2>nul
echo.
echo Done. Full P160 resume needs rebuild_bloom.bat ^(-k 512, ~30 min^).
echo Light P160 uses -k %K_FACTOR_LIGHT% ^(~2 GB class^).
pause
