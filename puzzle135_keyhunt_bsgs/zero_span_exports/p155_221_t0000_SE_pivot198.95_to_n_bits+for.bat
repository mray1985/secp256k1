@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 zero-span BSGS  top=0x1d271e07f0b379  tz=2^102
echo stage=SE_pivot198.95_to_n_bits+form56_mul_sqrt_pN_frac
echo tile 0/1180591620717411303423  range 749c781fc2cde40000000000000000000000000:749c781fc2cde400000000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 749c781fc2cde40000000000000000000000000:749c781fc2cde400000000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
