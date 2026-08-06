@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 SINGLE-SPAN BSGS  top=0x2000000464de13f59e9d  tz=2^82
echo stage=SE_pivot198.0_minus8+form56_div_2^H2
echo span=2^82  m=2^41  suggested -k 17179869184
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 8000001193784fd67a7400000000000000000000:8000001193784fd67a77ffffffffffffffffffff -k 17179869184 -t %THREADS% -s %STATS% -q
pause
