@echo off
REM Puzzle 135 — Kangaroo on 125-bit window from pipeline shelf2 anchor
cd /d C:\Users\mitch\Desktop\secp256k1\Kangaroo
Kangaroo.exe -t 4 -d 22 -w p135_shelf2.work -wi 300 -o p135_shelf2_result.txt ..\ECDLP\kangaroo_infiles\p135_shelf2_125bit.txt
pause
