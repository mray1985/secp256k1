@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 SINGLE-SPAN BSGS  top=0x10000128a8fa8708e61  tz=2^82
echo stage=SE_pivot198.95_minus8+form56_div_2^H2
echo span=2^82  m=2^41  suggested -k 17179869184
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 400004a2a3ea1c2398400000000000000000000:400004a2a3ea1c23987ffffffffffffffffffff -k 17179869184 -t %THREADS% -s %STATS% -q
pause
