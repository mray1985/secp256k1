@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 zero-span BSGS  top=0x1d271e07f0b379  tz=2^107
echo stage=SE_pivot198.95_to_n_bits+form56_mul_sqrt_pN_frac
echo tile 0/37778931862957161709567  range e938f03f859bc800000000000000000000000000:e938f03f859bc8000000000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r e938f03f859bc800000000000000000000000000:e938f03f859bc8000000000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
