@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 zero-span BSGS  top=0x800000d271e07f0b379  tz=2^79
echo stage=SE_pivot198.0_minus8_floor+form56_mul_sqrt_pN_frac
echo tile 0/140737488355327  range 4000006938f03f859bc80000000000000000000:4000006938f03f859bc800000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 4000006938f03f859bc80000000000000000000:4000006938f03f859bc800000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
