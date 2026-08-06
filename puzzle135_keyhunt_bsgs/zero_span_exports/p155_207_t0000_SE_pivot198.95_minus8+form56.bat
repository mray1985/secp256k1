@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 zero-span BSGS  top=0x8000044ba3fb3eea33  tz=2^83
echo stage=SE_pivot198.95_minus8+form56_mul_sqrt_pN_frac
echo tile 0/2251799813685247  range 40000225d1fd9f7519800000000000000000000:40000225d1fd9f75198000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 40000225d1fd9f7519800000000000000000000:40000225d1fd9f75198000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
