#!/usr/bin/env bash
# P160 BSGS dance @ -k 512 using EXISTING bloom cache
set -euo pipefail

ROOT="/mnt/c/Users/mitch/Desktop/secp256k1"
KEYHUNT="$ROOT/keyhunt_src/keyhunt"
# Prebuilt -k 512 blooms live here (do not rebuild)
WORKDIR="/mnt/c/Users/mitch/source/repos/keyhunt"
PUBFILE="$WORKDIR/P160.pub"
LOG="$WORKDIR/p160_dance_k512_run.log"

pkill -f 'keyhunt -m bsgs' 2>/dev/null || true
sleep 1

cp -f "$ROOT/puzzle160_keyhunt_bsgs/P160.pub" "$PUBFILE"
cd "$WORKDIR"

echo "WORKDIR=$WORKDIR"
ls -lah keyhunt_bsgs_4_2147483648.blm keyhunt_bsgs_6_67108864.blm keyhunt_bsgs_7_2097152.blm keyhunt_bsgs_2_2097152.tbl
free -h
echo "Launching: -k 512 -B dance (expect Reading bloom...)"
echo

"$KEYHUNT" \
  -m bsgs \
  -f "$PUBFILE" \
  -b 160 \
  -B dance \
  -k 512 \
  -t "$(nproc)" \
  -s 10 \
  -S \
  -q \
  2>&1 | tee -a "$LOG"
