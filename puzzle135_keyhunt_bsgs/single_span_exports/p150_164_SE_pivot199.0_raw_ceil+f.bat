@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 SINGLE-SPAN BSGS  top=0x41c63061b50a139  tz=2^91
echo stage=SE_pivot199.0_raw_ceil+form56_div_2^H2
echo span=2^91  m=2^46  suggested -k 549755813888
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 20e31830da8509c80000000000000000000000:20e31830da8509cfffffffffffffffffffffff -k 549755813888 -t %THREADS% -s %STATS% -q
pause
