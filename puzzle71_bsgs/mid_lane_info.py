#!/usr/bin/env python3
"""Print mid-band 2^29 window constants for TARGET.txt / build bat."""
from p71_common import END_R_MID_2P29, LO, M_2P29, MID_R, START_R_MID_2P29

print(f"start_r={START_R_MID_2P29}")
print(f"end_r={END_R_MID_2P29}")
print(f"mid_r={MID_R}")
print(f"d_lo={LO + START_R_MID_2P29}")
print(f"d_hi={LO + END_R_MID_2P29 - 1}")
print(f"gb={M_2P29 * 25 / 1e9:.2f}")
