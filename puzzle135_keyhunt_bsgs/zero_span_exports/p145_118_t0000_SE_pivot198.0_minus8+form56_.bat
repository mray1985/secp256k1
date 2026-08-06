@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 zero-span BSGS  top=0x400449b8a1b2bcd3  tz=2^82
echo stage=SE_pivot198.0_minus8+form56_div_2^H2
echo tile 0/1125899906842623  range 1001126e286caf34c00000000000000000000:1001126e286caf34c000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 1001126e286caf34c00000000000000000000:1001126e286caf34c000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
