@echo off
setlocal
call "%~dp0paths.bat"
cd /d "%WORKDIR%"
echo Leader px_w0  center=1016161246378405429915312532485865240202132152583
echo Range b1fe3f079b1aa9f8d2a98cd7ba726853cdc85107:b1fe3f079b1aa9f8d2a98cd7ba726a2577127107  (+-1000000000000)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r b1fe3f079b1aa9f8d2a98cd7ba726853cdc85107:b1fe3f079b1aa9f8d2a98cd7ba726a2577127107 -k %BLOOM_KB% -t %THREADS% -s %STATS% -S -q
pause
