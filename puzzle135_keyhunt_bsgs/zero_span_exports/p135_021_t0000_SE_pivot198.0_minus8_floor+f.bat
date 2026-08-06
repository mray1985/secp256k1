@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 zero-span BSGS  top=0x32095afcfa3abb  tz=2^81
echo stage=SE_pivot198.0_minus8_floor+form56_mul_2^H2
echo tile 0/562949953421311  range 6412b5f9f4757600000000000000000000:6412b5f9f47576000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P135_compressed.pub" -r 6412b5f9f4757600000000000000000000:6412b5f9f47576000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
