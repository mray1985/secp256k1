@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 zero-span BSGS  top=0x4004f7cf4034afc3  tz=2^92
echo stage=SE_pivot199.0_raw+form56_div_2^H2
echo tile 0/1152921504606846975  range 4004f7cf4034afc300000000000000000000000:4004f7cf4034afc3000000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 4004f7cf4034afc300000000000000000000000:4004f7cf4034afc3000000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
