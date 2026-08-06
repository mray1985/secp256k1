#!/usr/bin/env bash
set -u
pgrep -af status_every_2min || echo no_mon
pgrep -af 'keyhunt -m' || echo no_kh
free -h
LOG=/root/keyhunt_p160_bsgs_k4096/run.log
if [[ -f "$LOG" ]]; then
  tr '\r' '\n' < "$LOG" | grep -E 'processing|Bloom filter for|K factor|Mode BSGS' | tail -10
fi
