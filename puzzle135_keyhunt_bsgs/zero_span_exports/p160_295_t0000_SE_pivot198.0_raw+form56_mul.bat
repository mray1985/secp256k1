@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 zero-span BSGS  top=0x200005957273d4bc1d  tz=2^90
echo stage=SE_pivot198.0_raw+form56_mul_2^H2
echo tile 0/288230376151711743  range 80001655c9cf52f0740000000000000000000000:80001655c9cf52f07400000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 80001655c9cf52f0740000000000000000000000:80001655c9cf52f07400000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
