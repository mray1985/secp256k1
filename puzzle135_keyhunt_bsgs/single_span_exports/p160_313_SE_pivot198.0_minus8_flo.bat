@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 SINGLE-SPAN BSGS  top=0x10000000d271e07f0b379  tz=2^79
echo stage=SE_pivot198.0_minus8_floor+form56_mul_sqrt_pN_frac
echo span=2^79  m=2^40  suggested -k 8589934592
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 80000006938f03f859bc80000000000000000000:80000006938f03f859bcffffffffffffffffffff -k 8589934592 -t %THREADS% -s %STATS% -q
pause
