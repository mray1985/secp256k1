@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 SINGLE-SPAN BSGS  top=0x800013d02e40e87b23  tz=2^88
echo stage=SE_pivot198.0_raw
echo span=2^88  m=2^44  suggested -k 137438953472
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 800013d02e40e87b230000000000000000000000:800013d02e40e87b23ffffffffffffffffffffff -k 137438953472 -t %THREADS% -s %STATS% -q
pause
