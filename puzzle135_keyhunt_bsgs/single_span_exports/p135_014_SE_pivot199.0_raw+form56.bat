@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 SINGLE-SPAN BSGS  top=0x1ea2742f79c4e5  tz=2^82
echo stage=SE_pivot199.0_raw+form56_mul_sqrt_pN_frac
echo span=2^82  m=2^41  suggested -k 17179869184
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P135_compressed.pub" -r 7a89d0bde7139400000000000000000000:7a89d0bde71397ffffffffffffffffffff -k 17179869184 -t %THREADS% -s %STATS% -q
pause
