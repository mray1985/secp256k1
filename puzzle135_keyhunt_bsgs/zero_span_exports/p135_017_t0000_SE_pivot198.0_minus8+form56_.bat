@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 zero-span BSGS  top=0x350135e08d0f99  tz=2^81
echo stage=SE_pivot198.0_minus8+form56_mul_2^H2
echo tile 0/562949953421311  range 6a026bc11a1f3200000000000000000000:6a026bc11a1f32000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P135_compressed.pub" -r 6a026bc11a1f3200000000000000000000:6a026bc11a1f32000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
