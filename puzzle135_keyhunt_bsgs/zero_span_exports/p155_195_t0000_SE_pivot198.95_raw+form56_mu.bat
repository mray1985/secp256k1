@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 zero-span BSGS  top=0x80044ba3fb3eea33  tz=2^91
echo stage=SE_pivot198.95_raw+form56_mul_sqrt_pN_frac
echo tile 0/576460752303423487  range 400225d1fd9f751980000000000000000000000:400225d1fd9f7519800000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 400225d1fd9f751980000000000000000000000:400225d1fd9f7519800000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
