@echo off
setlocal
call "%~dp0paths.bat"
cd /d "%WORKDIR%"
echo Leader rmd_wrap2  center=999836400474710041910519435328613735285013260936
echo Range af2236fd42e33d142680a2d5ee8d4b9eb5b19a88:af2236fd42e33d142680a2d5ee8d4d705efbba88  (+-1000000000000)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r af2236fd42e33d142680a2d5ee8d4b9eb5b19a88:af2236fd42e33d142680a2d5ee8d4d705efbba88 -k %BLOOM_KB% -t %THREADS% -s %STATS% -S -q
pause
