@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 zero-span BSGS  top=0x100128a8fa8708e61  tz=2^90
echo stage=SE_pivot198.95_raw+form56_div_2^H2
echo tile 0/288230376151711743  range 4004a2a3ea1c239840000000000000000000000:4004a2a3ea1c2398400000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 4004a2a3ea1c239840000000000000000000000:4004a2a3ea1c2398400000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
