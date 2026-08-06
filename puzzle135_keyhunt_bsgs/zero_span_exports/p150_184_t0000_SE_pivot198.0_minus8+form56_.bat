@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 zero-span BSGS  top=0x100012166374c8b68f  tz=2^81
echo stage=SE_pivot198.0_minus8+form56_mul_2^H2
echo tile 0/562949953421311  range 2000242cc6e9916d1e00000000000000000000:2000242cc6e9916d1e000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 2000242cc6e9916d1e00000000000000000000:2000242cc6e9916d1e000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
