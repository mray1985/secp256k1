@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 SINGLE-SPAN BSGS  top=0x20000126a4322cd9ebb  tz=2^81
echo stage=SE_pivot199.0_minus8+form56_mul_sqrt_pN_frac
echo span=2^81  m=2^41  suggested -k 17179869184
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 4000024d486459b3d7600000000000000000000:4000024d486459b3d77ffffffffffffffffffff -k 17179869184 -t %THREADS% -s %STATS% -q
pause
