@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 zero-span BSGS  top=0x8fe4f672767acb  tz=2^89
echo stage=SE_pivot199.0_raw+form56_mul_sqrt_pN_frac
echo tile 0/144115188075855871  range 11fc9ece4ecf5960000000000000000000000:11fc9ece4ecf59600000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 11fc9ece4ecf5960000000000000000000000:11fc9ece4ecf59600000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
