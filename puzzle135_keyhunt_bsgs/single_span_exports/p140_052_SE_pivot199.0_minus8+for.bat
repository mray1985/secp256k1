@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 SINGLE-SPAN BSGS  top=0x237f11a2b69623  tz=2^86
echo stage=SE_pivot199.0_minus8+form56_mul_2^H2
echo span=2^86  m=2^43  suggested -k 68719476736
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r 8dfc468ada588c000000000000000000000:8dfc468ada588ffffffffffffffffffffff -k 68719476736 -t %THREADS% -s %STATS% -q
pause
