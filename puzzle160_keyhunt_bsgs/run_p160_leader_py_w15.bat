@echo off
setlocal
call "%~dp0paths.bat"
cd /d "%WORKDIR%"
echo Leader py_w15  center=803505878170136640646881328233715742298136844352
echo Range 8cbe731f9a8ed631b90b6c073feeaffc3a8a0840:8cbe731f9a8ed631b90b6c073feeb1cde3d42840  (+-1000000000000)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 8cbe731f9a8ed631b90b6c073feeaffc3a8a0840:8cbe731f9a8ed631b90b6c073feeb1cde3d42840 -k %BLOOM_KB% -t %THREADS% -s %STATS% -S -q
pause
