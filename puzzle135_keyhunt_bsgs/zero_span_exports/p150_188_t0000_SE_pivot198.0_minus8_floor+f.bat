@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 zero-span BSGS  top=0x100012095afcfa3abb  tz=2^81
echo stage=SE_pivot198.0_minus8_floor+form56_mul_2^H2
echo tile 0/562949953421311  range 20002412b5f9f4757600000000000000000000:20002412b5f9f47576000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 20002412b5f9f4757600000000000000000000:20002412b5f9f47576000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
