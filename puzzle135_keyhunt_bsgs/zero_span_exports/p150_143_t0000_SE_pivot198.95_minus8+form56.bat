@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 zero-span BSGS  top=0x1000189cff964876c9  tz=2^81
echo stage=SE_pivot198.95_minus8+form56_mul_sqrt_pN_frac
echo tile 0/562949953421311  range 20003139ff2c90ed9200000000000000000000:20003139ff2c90ed92000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 20003139ff2c90ed9200000000000000000000:20003139ff2c90ed92000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
