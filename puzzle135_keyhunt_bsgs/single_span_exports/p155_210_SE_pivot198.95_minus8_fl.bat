@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 SINGLE-SPAN BSGS  top=0x200001c63061b50a139  tz=2^81
echo stage=SE_pivot198.95_minus8_floor+form56_div_2^H2
echo span=2^81  m=2^41  suggested -k 17179869184
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 4000038c60c36a1427200000000000000000000:4000038c60c36a14273ffffffffffffffffffff -k 17179869184 -t %THREADS% -s %STATS% -q
pause
