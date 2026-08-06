@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 zero-span BSGS  top=0x234320f93ee8f9  tz=2^86
echo stage=SE_pivot198.95_minus8+form56_mul_2^H2
echo tile 0/18014398509481983  range 8d0c83e4fba3e4000000000000000000000:8d0c83e4fba3e40000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r 8d0c83e4fba3e4000000000000000000000:8d0c83e4fba3e40000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
