@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 SINGLE-SPAN BSGS  top=0x80044ba3fb3eea33  tz=2^91
echo stage=SE_pivot198.95_raw+form56_mul_sqrt_pN_frac
echo span=2^91  m=2^46  suggested -k 549755813888
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 400225d1fd9f751980000000000000000000000:400225d1fd9f7519fffffffffffffffffffffff -k 549755813888 -t %THREADS% -s %STATS% -q
pause
