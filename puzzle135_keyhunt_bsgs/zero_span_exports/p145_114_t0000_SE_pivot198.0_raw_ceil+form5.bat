@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 zero-span BSGS  top=0x11c63061b50a139  tz=2^88
echo stage=SE_pivot198.0_raw_ceil+form56_div_2^H2
echo tile 0/72057594037927935  range 11c63061b50a1390000000000000000000000:11c63061b50a13900000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 11c63061b50a1390000000000000000000000:11c63061b50a13900000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
