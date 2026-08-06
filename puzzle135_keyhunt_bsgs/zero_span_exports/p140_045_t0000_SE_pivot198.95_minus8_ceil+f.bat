@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 zero-span BSGS  top=0x10d271e07f0b379  tz=2^83
echo stage=SE_pivot198.95_minus8_ceil+form56_mul_sqrt_pN_frac
echo tile 0/2251799813685247  range 86938f03f859bc800000000000000000000:86938f03f859bc8000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r 86938f03f859bc800000000000000000000:86938f03f859bc8000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
