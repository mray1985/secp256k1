@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 zero-span BSGS  top=0x1449b8a1b2bcd3  tz=2^92
echo stage=SE_pivot199.0_raw+form56_div_2^H2
echo tile 0/1152921504606846975  range 1449b8a1b2bcd300000000000000000000000:1449b8a1b2bcd3000000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 1449b8a1b2bcd300000000000000000000000:1449b8a1b2bcd3000000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
