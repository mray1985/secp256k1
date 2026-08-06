@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 SINGLE-SPAN BSGS  top=0x40d271e07f0b379  tz=2^91
echo stage=SE_pivot199.0_raw_ceil+form56_mul_sqrt_pN_frac
echo span=2^91  m=2^46  suggested -k 549755813888
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 206938f03f859bc80000000000000000000000:206938f03f859bcfffffffffffffffffffffff -k 549755813888 -t %THREADS% -s %STATS% -q
pause
