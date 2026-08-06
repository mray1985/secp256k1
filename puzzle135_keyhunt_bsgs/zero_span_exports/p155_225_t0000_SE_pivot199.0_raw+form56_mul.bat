@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 zero-span BSGS  top=0x200126a4322cd9ebb  tz=2^89
echo stage=SE_pivot199.0_raw+form56_mul_sqrt_pN_frac
echo tile 0/144115188075855871  range 40024d486459b3d760000000000000000000000:40024d486459b3d7600000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 40024d486459b3d760000000000000000000000:40024d486459b3d7600000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
