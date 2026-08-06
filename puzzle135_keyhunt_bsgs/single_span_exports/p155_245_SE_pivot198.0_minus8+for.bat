@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 SINGLE-SPAN BSGS  top=0x80000126a4322cd9ebb  tz=2^79
echo stage=SE_pivot198.0_minus8+form56_mul_sqrt_pN_frac
echo span=2^79  m=2^40  suggested -k 8589934592
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 400000935219166cf5d80000000000000000000:400000935219166cf5dffffffffffffffffffff -k 8589934592 -t %THREADS% -s %STATS% -q
pause
