@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 zero-span BSGS  top=0x80000b33619a93bdf9  tz=2^83
echo stage=SE_pivot199.0_minus8
echo tile 0/2251799813685247  range 40000599b0cd49defc800000000000000000000:40000599b0cd49defc8000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 40000599b0cd49defc800000000000000000000:40000599b0cd49defc8000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
