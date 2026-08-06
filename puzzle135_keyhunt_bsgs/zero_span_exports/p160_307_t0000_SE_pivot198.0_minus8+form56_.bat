@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 zero-span BSGS  top=0x20000005957273d4bc1d  tz=2^82
echo stage=SE_pivot198.0_minus8+form56_mul_2^H2
echo tile 0/1125899906842623  range 8000001655c9cf52f07400000000000000000000:8000001655c9cf52f074000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 8000001655c9cf52f07400000000000000000000:8000001655c9cf52f074000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
