@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 SINGLE-SPAN BSGS  top=0x8001a8f82f04b4805  tz=2^82
echo stage=SE_pivot198.95_minus8+form56_div_2^H2
echo span=2^82  m=2^41  suggested -k 17179869184
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 20006a3e0bc12d201400000000000000000000:20006a3e0bc12d2017ffffffffffffffffffff -k 17179869184 -t %THREADS% -s %STATS% -q
pause
