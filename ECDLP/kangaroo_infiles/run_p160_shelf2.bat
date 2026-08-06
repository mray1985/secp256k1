@echo off
REM Puzzle 160 — Kangaroo on 125-bit window from pipeline shelf2 (official P160 pubkey)
cd /d C:\Users\mitch\Desktop\secp256k1\Kangaroo
Kangaroo.exe -t 4 -d 22 -w p160_shelf2.work -wi 300 -o p160_shelf2_result.txt ..\ECDLP\kangaroo_infiles\p160_shelf2_125bit.txt
pause
