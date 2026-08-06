@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 SINGLE-SPAN BSGS  top=0x41602d0e088f5fb  tz=2^81
echo stage=SE_pivot198.0_minus8+form56_div_2^H2
echo span=2^81  m=2^41  suggested -k 17179869184
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r 82c05a1c111ebf600000000000000000000:82c05a1c111ebf7ffffffffffffffffffff -k 17179869184 -t %THREADS% -s %STATS% -q
pause
