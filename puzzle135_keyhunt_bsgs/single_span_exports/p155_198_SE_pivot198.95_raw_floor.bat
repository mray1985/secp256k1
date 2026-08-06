@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 SINGLE-SPAN BSGS  top=0x2001c63061b50a139  tz=2^89
echo stage=SE_pivot198.95_raw_floor+form56_div_2^H2
echo span=2^89  m=2^45  suggested -k 274877906944
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 40038c60c36a142720000000000000000000000:40038c60c36a14273ffffffffffffffffffffff -k 274877906944 -t %THREADS% -s %STATS% -q
pause
