@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 zero-span BSGS  top=0x837f11a2b69623  tz=2^84
echo stage=SE_pivot198.0_minus8+form56_mul_2^H2
echo tile 0/4503599627370495  range 837f11a2b69623000000000000000000000:837f11a2b696230000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r 837f11a2b69623000000000000000000000:837f11a2b696230000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
