@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 SINGLE-SPAN BSGS  top=0x350135e08d0f99  tz=2^81
echo stage=SE_pivot198.0_minus8+form56_mul_2^H2
echo span=2^81  m=2^41  suggested -k 17179869184
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P135_compressed.pub" -r 6a026bc11a1f3200000000000000000000:6a026bc11a1f33ffffffffffffffffffff -k 17179869184 -t %THREADS% -s %STATS% -q
pause
