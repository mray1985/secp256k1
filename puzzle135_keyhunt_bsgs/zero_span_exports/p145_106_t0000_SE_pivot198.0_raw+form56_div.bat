@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 zero-span BSGS  top=0x4449b8a1b2bcd3  tz=2^90
echo stage=SE_pivot198.0_raw+form56_div_2^H2
echo tile 0/288230376151711743  range 11126e286caf34c0000000000000000000000:11126e286caf34c00000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 11126e286caf34c0000000000000000000000:11126e286caf34c00000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
