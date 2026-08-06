@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 zero-span BSGS  top=0x100449b8a1b2bcd3  tz=2^84
echo stage=SE_pivot199.0_minus8+form56_div_2^H2
echo tile 0/4503599627370495  range 100449b8a1b2bcd3000000000000000000000:100449b8a1b2bcd30000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 100449b8a1b2bcd3000000000000000000000:100449b8a1b2bcd30000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
