@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 zero-span BSGS  top=0x2008006b93b442f9  tz=2^83
echo stage=SE_pivot198.95_minus8+form56_div_2^H2
echo tile 0/2251799813685247  range 10040035c9da217c800000000000000000000:10040035c9da217c8000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 10040035c9da217c800000000000000000000:10040035c9da217c8000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
