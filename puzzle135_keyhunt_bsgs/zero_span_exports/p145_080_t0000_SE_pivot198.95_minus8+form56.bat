@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 zero-span BSGS  top=0x200a2b11cd66da87  tz=2^83
echo stage=SE_pivot198.95_minus8+form56_mul_2^H2
echo tile 0/2251799813685247  range 10051588e6b36d43800000000000000000000:10051588e6b36d438000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 10051588e6b36d43800000000000000000000:10051588e6b36d438000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
