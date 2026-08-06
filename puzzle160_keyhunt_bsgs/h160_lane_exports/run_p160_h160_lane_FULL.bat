@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo h160 lane export: FULL (one-shot entire lane)
echo q_h=138614061598878480877088849141041944608  eps_h=2567541394  h160_bf=0.814700232
echo lo_lane=1326093679998364004747100419105194353283569811456  hi_lane=1326093679998364004747100419105194353287864778751
echo Range e84818e1bf7f699aa6e28ef9edfb482100000000:e84818e1bf7f699aa6e28ef9edfb582100000000  span=17592186044417  (KeyHunt min span 100000000000)
REM Bloom already built in WORKDIR — do not pass -S (saves ~30 min + 8 GB rewrite per window)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r e84818e1bf7f699aa6e28ef9edfb482100000000:e84818e1bf7f699aa6e28ef9edfb582100000000 -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
