@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 SINGLE-SPAN BSGS  top=0x1d271e07f0b379  tz=2^102
echo stage=SE_pivot198.95_to_n_bits+form56_mul_sqrt_pN_frac
echo span=2^102  m=2^51  suggested -k 17592186044416
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 749c781fc2cde40000000000000000000000000:749c781fc2cde7fffffffffffffffffffffffff -k 17592186044416 -t %THREADS% -s %STATS% -q
pause
