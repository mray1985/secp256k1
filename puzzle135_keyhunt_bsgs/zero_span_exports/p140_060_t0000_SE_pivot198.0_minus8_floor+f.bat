@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 zero-span BSGS  top=0x412095afcfa3abb  tz=2^81
echo stage=SE_pivot198.0_minus8_floor+form56_mul_2^H2
echo tile 0/562949953421311  range 82412b5f9f4757600000000000000000000:82412b5f9f47576000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r 82412b5f9f4757600000000000000000000:82412b5f9f47576000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
