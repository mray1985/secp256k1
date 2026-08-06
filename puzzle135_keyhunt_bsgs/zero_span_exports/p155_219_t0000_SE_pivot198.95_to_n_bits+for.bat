@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 zero-span BSGS  top=0x12095afcfa3abb  tz=2^102
echo stage=SE_pivot198.95_to_n_bits+form56_mul_2^H2
echo tile 0/1180591620717411303423  range 48256bf3e8eaec0000000000000000000000000:48256bf3e8eaec00000000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 48256bf3e8eaec0000000000000000000000000:48256bf3e8eaec00000000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
