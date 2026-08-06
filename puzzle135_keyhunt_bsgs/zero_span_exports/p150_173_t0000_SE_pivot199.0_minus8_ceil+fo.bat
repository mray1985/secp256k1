@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 zero-span BSGS  top=0x4000d271e07f0b379  tz=2^83
echo stage=SE_pivot199.0_minus8_ceil+form56_mul_sqrt_pN_frac
echo tile 0/2251799813685247  range 20006938f03f859bc800000000000000000000:20006938f03f859bc8000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 20006938f03f859bc800000000000000000000:20006938f03f859bc8000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
