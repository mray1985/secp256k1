@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 zero-span BSGS  top=0x1c63061b50a139  tz=2^102
echo stage=SE_pivot198.95_to_n_bits+form56_div_2^H2
echo tile 0/1180591620717411303423  range 718c186d4284e40000000000000000000000000:718c186d4284e400000000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 718c186d4284e40000000000000000000000000:718c186d4284e400000000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
