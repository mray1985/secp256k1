@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 zero-span BSGS  top=0x41602d0e088f5fb  tz=2^81
echo stage=SE_pivot198.0_minus8+form56_div_2^H2
echo tile 0/562949953421311  range 82c05a1c111ebf600000000000000000000:82c05a1c111ebf6000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r 82c05a1c111ebf600000000000000000000:82c05a1c111ebf6000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
