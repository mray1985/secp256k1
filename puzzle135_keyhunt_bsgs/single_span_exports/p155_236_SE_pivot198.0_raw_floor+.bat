@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 SINGLE-SPAN BSGS  top=0x8001c63061b50a139  tz=2^87
echo stage=SE_pivot198.0_raw_floor+form56_div_2^H2
echo span=2^87  m=2^44  suggested -k 137438953472
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 4000e31830da8509c8000000000000000000000:4000e31830da8509cffffffffffffffffffffff -k 137438953472 -t %THREADS% -s %STATS% -q
pause
