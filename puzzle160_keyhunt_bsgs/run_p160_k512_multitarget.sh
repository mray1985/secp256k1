#!/usr/bin/env bash
# P160 BSGS dance @ -k 512 with multi-target pubs (cached bloom)
set -euo pipefail

ROOT="/mnt/c/Users/mitch/Desktop/secp256k1"
KEYHUNT="$ROOT/keyhunt_src/keyhunt"
WORKDIR="/mnt/c/Users/mitch/source/repos/keyhunt"
PUBFILE="$WORKDIR/P160_dance_multitarget.pub"
LOG="$WORKDIR/p160_dance_k512_multitarget_run.log"

# stop prior dance (ignore errors)
kill $(pgrep -f 'keyhunt -m bsgs') 2>/dev/null || true
sleep 2

cp -f "$ROOT/puzzle160_keyhunt_bsgs/P160_dance_multitarget.pub" "$PUBFILE"
cd "$WORKDIR"

echo "targets: $(grep -c '^04' "$PUBFILE")"
echo "Launching multitarget dance -k 512"
free -h

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
