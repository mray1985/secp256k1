@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 SINGLE-SPAN BSGS  top=0x1d271e07f0b379  tz=2^87
echo stage=SE_pivot198.95_to_n_bits+form56_mul_sqrt_pN_frac
echo span=2^87  m=2^44  suggested -k 137438953472
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r e938f03f859bc8000000000000000000000:e938f03f859bcffffffffffffffffffffff -k 137438953472 -t %THREADS% -s %STATS% -q
pause
