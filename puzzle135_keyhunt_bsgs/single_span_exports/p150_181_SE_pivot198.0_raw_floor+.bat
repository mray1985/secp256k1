@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 SINGLE-SPAN BSGS  top=0x201c63061b50a139  tz=2^88
echo stage=SE_pivot198.0_raw_floor+form56_div_2^H2
echo span=2^88  m=2^44  suggested -k 137438953472
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 201c63061b50a1390000000000000000000000:201c63061b50a139ffffffffffffffffffffff -k 137438953472 -t %THREADS% -s %STATS% -q
pause
