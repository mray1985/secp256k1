@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 SINGLE-SPAN BSGS  top=0x1c63061b50a139  tz=2^97
echo stage=SE_pivot198.95_to_n_bits+form56_div_2^H2
echo span=2^97  m=2^49  suggested -k 4398046511104
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 38c60c36a14272000000000000000000000000:38c60c36a14273ffffffffffffffffffffffff -k 4398046511104 -t %THREADS% -s %STATS% -q
pause
