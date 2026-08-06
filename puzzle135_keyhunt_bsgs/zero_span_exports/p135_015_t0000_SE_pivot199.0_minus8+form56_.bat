@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 zero-span BSGS  top=0x3ea2742f79c4e5  tz=2^81
echo stage=SE_pivot199.0_minus8+form56_mul_sqrt_pN_frac
echo tile 0/562949953421311  range 7d44e85ef389ca00000000000000000000:7d44e85ef389ca000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P135_compressed.pub" -r 7d44e85ef389ca00000000000000000000:7d44e85ef389ca000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
