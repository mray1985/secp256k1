@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 zero-span BSGS  top=0x20000126a4322cd9ebb  tz=2^81
echo stage=SE_pivot199.0_minus8+form56_mul_sqrt_pN_frac
echo tile 0/562949953421311  range 4000024d486459b3d7600000000000000000000:4000024d486459b3d76000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 4000024d486459b3d7600000000000000000000:4000024d486459b3d76000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
