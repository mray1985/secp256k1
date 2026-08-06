@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 SINGLE-SPAN BSGS  top=0x80000b33619a93bdf9  tz=2^83
echo stage=SE_pivot199.0_minus8
echo span=2^83  m=2^42  suggested -k 34359738368
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 40000599b0cd49defc800000000000000000000:40000599b0cd49defcfffffffffffffffffffff -k 34359738368 -t %THREADS% -s %STATS% -q
pause
