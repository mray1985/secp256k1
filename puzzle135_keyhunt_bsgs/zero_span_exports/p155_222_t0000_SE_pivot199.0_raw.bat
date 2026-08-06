@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 zero-span BSGS  top=0x800b33619a93bdf9  tz=2^91
echo stage=SE_pivot199.0_raw
echo tile 0/576460752303423487  range 400599b0cd49defc80000000000000000000000:400599b0cd49defc800000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 400599b0cd49defc80000000000000000000000:400599b0cd49defc800000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
