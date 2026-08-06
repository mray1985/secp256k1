#!/usr/bin/env bash
# Puzzle 160 keyhunt BSGS — both ends + random middle bounce
# Endomorphism (-e) is NOT supported in bsgs mode (address/rmd160/vanity/xpoint only).
set -euo pipefail

ROOT="/mnt/c/Users/mitch/Desktop/secp256k1"
SRC="$ROOT/keyhunt_src"
PUBDIR="$ROOT/puzzle160_keyhunt_bsgs"
# Native Linux FS for bloom/tables (~59GB class at -k 4096; will thrash swap on 15GB RAM)
K="${K_FACTOR:-4096}"
WORKDIR="${HOME}/keyhunt_p160_bsgs_k${K}"
KEYHUNT="$SRC/keyhunt"
PUBFILE="$WORKDIR/P160.pub"
LOG="$WORKDIR/run.log"

mkdir -p "$WORKDIR"
cd "$WORKDIR"

# Uncompressed pubkey (BSGS needs 04||X||Y)
cp -f "$PUBDIR/P160.pub" "$PUBFILE"

# Record signature r alongside (informational; BSGS target is the pubkey)
python3 <<'PY'
import sys
sys.path.insert(0, "/mnt/c/Users/mitch/Desktop/secp256k1")
from scan_log_ratio_cross_puzzle import load_rows
rr = {r.n: r for r in load_rows()}[160]
open("P160_r.txt", "w").write(f"{rr.r:064x}\n")
open("P160_targets_note.txt", "w").write(
    "BSGS target: P160.pub (uncompressed puzzle pubkey)\n"
    f"signature r (Rx of kG) hex: {rr.r:064x}\n"
    "Note: r is NOT a second BSGS pubkey; logged for lane cross-ref only.\n"
    "Mode: -B dance = TOP (end) + BOTTOM (start) + random middle; shrinks as space closes.\n"
    "K=4096 (~59GB bloom class; max for default -n). Endomorphism N/A for bsgs.\n"
)
print(f"r={rr.r:064x}")
PY

# -B dance: rand%3 -> top / bottom / random-in-remaining-middle
# -k 4096 = AlbertoBSD max for default N; ~8x the k512 bloom (~59GB)
NPROC="$(nproc)"

echo "WORKDIR=$WORKDIR"
echo "KEYHUNT=$KEYHUNT"
echo "PUB=$(head -c 66 "$PUBFILE")..."
echo "free mem:"
free -h
echo
echo "Launching: bsgs -b 160 -B dance -k $K -t $NPROC -S"
echo "Endomorphism: skipped (keyhunt exits if -e with bsgs)"
echo

"$KEYHUNT" \
  -m bsgs \
  -f "$PUBFILE" \
  -b 160 \
  -B dance \
  -k "$K" \
  -t "$NPROC" \
  -s 10 \
  -S \
  -q \
  2>&1 | tee -a "$LOG"
