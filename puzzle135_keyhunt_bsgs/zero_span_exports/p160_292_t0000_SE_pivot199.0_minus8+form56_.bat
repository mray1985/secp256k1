@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 zero-span BSGS  top=0x800000464de13f59e9d  tz=2^84
echo stage=SE_pivot199.0_minus8+form56_div_2^H2
echo tile 0/4503599627370495  range 800000464de13f59e9d000000000000000000000:800000464de13f59e9d0000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 800000464de13f59e9d000000000000000000000:800000464de13f59e9d0000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
