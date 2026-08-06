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
set PUBFILE=%PUBDIR%P135_compressed.pub

REM P135 tax-math anchor BSGS: 2^32 windows, k=512 (~8 GB tables)
set K_FACTOR=512
set THREADS=%NUMBER_OF_PROCESSORS%
set STATS=10
