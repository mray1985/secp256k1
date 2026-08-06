@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 zero-span BSGS  top=0x108775f507d97f  tz=2^82
echo stage=SE_pivot199.0_raw+form56_div_2^H2
echo tile 0/1125899906842623  range 421dd7d41f65fc00000000000000000000:421dd7d41f65fc000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P135_compressed.pub" -r 421dd7d41f65fc00000000000000000000:421dd7d41f65fc000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
