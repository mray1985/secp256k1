@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 zero-span BSGS  top=0x34320f93ee8f9  tz=2^90
echo stage=SE_pivot198.95_raw+form56_mul_2^H2
echo tile 0/288230376151711743  range d0c83e4fba3e40000000000000000000000:d0c83e4fba3e400000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r d0c83e4fba3e40000000000000000000000:d0c83e4fba3e400000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
