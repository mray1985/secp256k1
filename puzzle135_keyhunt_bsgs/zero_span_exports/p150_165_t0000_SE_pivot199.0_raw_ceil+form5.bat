@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 zero-span BSGS  top=0x40d271e07f0b379  tz=2^91
echo stage=SE_pivot199.0_raw_ceil+form56_mul_sqrt_pN_frac
echo tile 0/576460752303423487  range 206938f03f859bc80000000000000000000000:206938f03f859bc800000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 206938f03f859bc80000000000000000000000:206938f03f859bc800000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
