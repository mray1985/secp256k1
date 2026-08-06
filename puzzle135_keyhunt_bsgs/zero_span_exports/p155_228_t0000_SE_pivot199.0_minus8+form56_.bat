@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 zero-span BSGS  top=0x400004f7cf4034afc3  tz=2^84
echo stage=SE_pivot199.0_minus8+form56_div_2^H2
echo tile 0/4503599627370495  range 400004f7cf4034afc3000000000000000000000:400004f7cf4034afc30000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 400004f7cf4034afc3000000000000000000000:400004f7cf4034afc30000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
