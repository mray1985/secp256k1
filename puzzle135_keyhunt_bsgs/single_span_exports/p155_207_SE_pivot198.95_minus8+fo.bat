@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 SINGLE-SPAN BSGS  top=0x8000044ba3fb3eea33  tz=2^83
echo stage=SE_pivot198.95_minus8+form56_mul_sqrt_pN_frac
echo span=2^83  m=2^42  suggested -k 34359738368
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 40000225d1fd9f7519800000000000000000000:40000225d1fd9f7519fffffffffffffffffffff -k 34359738368 -t %THREADS% -s %STATS% -q
pause
