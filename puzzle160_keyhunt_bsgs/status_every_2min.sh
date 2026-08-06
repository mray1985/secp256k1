#!/usr/bin/env bash
# Emit a one-line STATUS every 120s for the P160 k4096 keyhunt job.
set -u
LOG=/root/keyhunt_p160_bsgs_k4096/run.log
STAT=/root/keyhunt_p160_bsgs_k4096/status_every_2min.log
INTERVAL=120

while true; do
  ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  if pgrep -f 'keyhunt -m bsgs' >/dev/null 2>&1; then
    alive=ALIVE
    pid=$(pgrep -f 'keyhunt -m bsgs' | head -1)
  else
    alive=DEAD
    pid=-
  fi
  mem=$(free -h | awk '/^Mem:/{printf "mem_used=%s avail=%s",$3,$7}')
  swap=$(free -h | awk '/^Swap:/{printf "swap_used=%s free=%s",$3,$4}')
  prog=$(tr '\r' '\n' < "$LOG" 2>/dev/null | grep -E 'processing|Total|Found|Writing bloom|Reading bloom|keys in' | tail -1 | sed 's/^[[:space:]]*//')
  line="STATUS ts=$ts pid=$pid state=$alive $mem $swap | $prog"
  echo "$line" | tee -a "$STAT"
  sleep "$INTERVAL"
done
