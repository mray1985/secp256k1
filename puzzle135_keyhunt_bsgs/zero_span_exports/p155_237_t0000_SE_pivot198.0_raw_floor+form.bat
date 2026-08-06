@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 zero-span BSGS  top=0x8000d271e07f0b379  tz=2^87
echo stage=SE_pivot198.0_raw_floor+form56_mul_sqrt_pN_frac
echo tile 0/36028797018963967  range 40006938f03f859bc8000000000000000000000:40006938f03f859bc80000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 40006938f03f859bc8000000000000000000000:40006938f03f859bc80000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
