#!/usr/bin/env python3
"""Emit narrow KeyHunt BSGS launchers for barcode leader centers (band-aware span)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from puzzle160_complement_focus import DEFAULT_HALF_WINDOW, MIN_KEYHUNT_SPAN, clip_d_range

LEADERS = {
    "py_w15": 803505878170136640646881328233715742298136844352,
    "px_w0": 1016161246378405429915312532485865240202132152583,
    "y2_w21": 1279319893184270309653638302331043709986753761686,
    "rmd_wrap2": 999836400474710041910519435328613735285013260936,
}

HALF_WINDOW = DEFAULT_HALF_WINDOW


def main() -> None:
    out_dir = Path(__file__).resolve().parent
    for name, center in LEADERS.items():
        lo, hi, span = clip_d_range(center, HALF_WINDOW)
        bat = out_dir / f"run_p160_leader_{name}.bat"
        bat.write_text(
            f"""@echo off
setlocal
call "%~dp0paths.bat"
cd /d "%WORKDIR%"
echo Leader {name}  center={center}
echo Range {lo:x}:{hi:x}  span={span}  (KeyHunt min {MIN_KEYHUNT_SPAN:x})
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r {lo:x}:{hi:x} -k %K_FACTOR% -t %THREADS% -s %STATS% -S -q
pause
""",
            encoding="utf-8",
        )
        print(f"wrote {bat.name}  span={span}  {lo:x}:{hi:x}")


if __name__ == "__main__":
    main()
