@echo off
REM Test BSGS on candidate 1 with existing bloom files (k=512 -S).
setlocal
set ROOT=%~dp0
set PW=Z:\root\keyhunt-main\keyhunt-win-main\MinGW
set EXE=%PW%\keyhunt.exe
set PUB=%ROOT%puzzle135_keyhunt_bsgs\P135_compressed.pub
set OUT=%ROOT%bsgs_results\test_candidate_001.txt

if not exist "%EXE%" (
  echo [E] keyhunt not found at %EXE%
  pause
  exit /b 1
)

echo Keyhunt: %EXE%
echo Pub:     %PUB%
echo WorkDir: %PW%
echo.

for /f "tokens=8 delims=	" %%a in ('type "%ROOT%135kanga_2p65_candidates.tsv" ^| findstr /b "1	"') do set LO=%%a
for /f "tokens=9 delims=	" %%a in ('type "%ROOT%135kanga_2p65_candidates.tsv" ^| findstr /b "1	"') do set HI=%%a

echo Candidate 1 range:
echo   lo: 0x%LO%
echo   hi: 0x%HI%
echo.
echo Running: keyhunt -m bsgs -f P135_compressed.pub -r %LO%:%HI% -k 512 -S -t %NUMBER_OF_PROCESSORS% -s 10 -q
echo.

cd /d "%PW%"
"%EXE%" -m bsgs -f "%PUB%" -r "%LO%:%HI%" -k 512 -S -t %NUMBER_OF_PROCESSORS% -s 10 -q
echo.
echo Exit code: %ERRORLEVEL%
echo Output saved to %OUT%
pause
