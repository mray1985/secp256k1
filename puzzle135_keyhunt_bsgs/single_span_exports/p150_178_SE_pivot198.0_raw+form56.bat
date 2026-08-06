@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 SINGLE-SPAN BSGS  top=0x401a613e2bfa5a8d  tz=2^87
echo stage=SE_pivot198.0_raw+form56_mul_sqrt_pN_frac
echo span=2^87  m=2^44  suggested -k 137438953472
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 200d309f15fd2d468000000000000000000000:200d309f15fd2d46ffffffffffffffffffffff -k 137438953472 -t %THREADS% -s %STATS% -q
pause
