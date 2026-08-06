@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 SINGLE-SPAN BSGS  top=0x101c63061b50a139  tz=2^89
echo stage=SE_pivot198.95_raw_floor+form56_div_2^H2
echo span=2^89  m=2^45  suggested -k 274877906944
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 2038c60c36a142720000000000000000000000:2038c60c36a14273ffffffffffffffffffffff -k 274877906944 -t %THREADS% -s %STATS% -q
pause
