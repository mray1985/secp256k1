@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 zero-span BSGS  top=0x10000128a8fa8708e61  tz=2^82
echo stage=SE_pivot198.95_minus8+form56_div_2^H2
echo tile 0/1125899906842623  range 400004a2a3ea1c2398400000000000000000000:400004a2a3ea1c23984000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 400004a2a3ea1c2398400000000000000000000:400004a2a3ea1c23984000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
