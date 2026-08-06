@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 SINGLE-SPAN BSGS  top=0x20fe4f672767acb  tz=2^87
echo stage=SE_pivot198.0_raw+form56_mul_sqrt_pN_frac
echo span=2^87  m=2^44  suggested -k 137438953472
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 107f27b393b3d658000000000000000000000:107f27b393b3d65ffffffffffffffffffffff -k 137438953472 -t %THREADS% -s %STATS% -q
pause
