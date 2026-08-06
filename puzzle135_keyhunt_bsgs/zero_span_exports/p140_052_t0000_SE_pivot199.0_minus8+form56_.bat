@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 zero-span BSGS  top=0x237f11a2b69623  tz=2^86
echo stage=SE_pivot199.0_minus8+form56_mul_2^H2
echo tile 0/18014398509481983  range 8dfc468ada588c000000000000000000000:8dfc468ada588c0000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r 8dfc468ada588c000000000000000000000:8dfc468ada588c0000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
