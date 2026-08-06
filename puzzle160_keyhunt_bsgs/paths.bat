@echo off
REM KeyHunt install (ServerEdition MinGW — supports >64 GB RAM on Windows)
set KEYHUNT=Z:\root\keyhunt-main\keyhunt-win-main\MinGW\keyhunt.exe
set KEYHUNT_CYGWIN=Z:\root\keyhunt-main\keyhunt-win-main\CYGWIN\keyhunt.exe
set USEFUL=Z:\root\keyhunt-main\keyhunt-win-main\Useful
set KEYSUB=%USEFUL%\keysubtracter.exe
set B58DEC=%USEFUL%\b58dec.exe
set RMD_SORT=%USEFUL%\RMD160-Sort.exe

REM Bloom / table files are created in WORKDIR on first -S run
set WORKDIR=Z:\root\keyhunt-main\keyhunt-win-main\MinGW
set PUBDIR=%~dp0
set PUBFILE=%PUBDIR%P160_compressed.pub

REM --- Full profile (resume with run_p160_bsgs_7m.bat) ---
REM -k is K factor (decimal), NOT kilobytes. 512 ~ 8 GB BSGS tables + ~7.2 GB .blm on disk.
set K_FACTOR=512
set THREADS=4

REM --- Light profile (P71 / disk work — run_p160_bsgs_light.bat) ---
set K_FACTOR_LIGHT=128
set THREADS_LIGHT=1

set STATS=10
set P160_PAUSED=1
