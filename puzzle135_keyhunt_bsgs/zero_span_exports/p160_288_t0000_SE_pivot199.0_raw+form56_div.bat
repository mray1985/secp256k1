@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 zero-span BSGS  top=0x8000464de13f59e9d  tz=2^92
echo stage=SE_pivot199.0_raw+form56_div_2^H2
echo tile 0/1152921504606846975  range 8000464de13f59e9d00000000000000000000000:8000464de13f59e9d000000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 8000464de13f59e9d00000000000000000000000:8000464de13f59e9d000000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
