@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 zero-span BSGS  top=0x800fe4f672767acb  tz=2^81
echo stage=SE_pivot199.0_minus8+form56_mul_sqrt_pN_frac
echo tile 0/562949953421311  range 1001fc9ece4ecf59600000000000000000000:1001fc9ece4ecf596000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 1001fc9ece4ecf59600000000000000000000:1001fc9ece4ecf596000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
