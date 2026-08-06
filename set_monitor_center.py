#!/usr/bin/env python3
"""Center secondary monitor vertically on primary (Windows)."""

from __future__ import annotations

import sys

import win32api
import win32con

ENUM_CURRENT_SETTINGS = -1
CDS_UPDATEREGISTRY = 0x00000001
CDS_NORESET = 0x00000004
DISPLAY_DEVICE_ACTIVE = 0x00000001
DISPLAY_DEVICE_ATTACHED = 0x00000001


def load_active_displays() -> list[tuple[str, object]]:
    out: list[tuple[str, object]] = []
    i = 0
    while True:
        try:
            dev = win32api.EnumDisplayDevices(None, i)
        except win32api.error:
            break
        i += 1
        if not dev.StateFlags & DISPLAY_DEVICE_ATTACHED:
            continue
        mode = win32api.EnumDisplaySettings(dev.DeviceName, ENUM_CURRENT_SETTINGS)
        out.append((dev.DeviceName, mode))
    return out


def apply_positions(positions: dict[str, tuple[int, int, int, int]]) -> None:
    """positions: device -> (x, y, width, height)"""
    for name, (x, y, w, h) in positions.items():
        mode = win32api.EnumDisplaySettings(name, ENUM_CURRENT_SETTINGS)
        mode.PelsWidth = w
        mode.PelsHeight = h
        mode.Position_x = x
        mode.Position_y = y
        mode.Fields = (
            win32con.DM_PELSWIDTH
            | win32con.DM_PELSHEIGHT
            | win32con.DM_POSITION
        )
        rc = win32api.ChangeDisplaySettingsEx(name, mode, CDS_UPDATEREGISTRY | CDS_NORESET)
        if rc != win32con.DISP_CHANGE_SUCCESSFUL:
            raise RuntimeError(f"ChangeDisplaySettingsEx({name}) -> {rc}")
    rc = win32api.ChangeDisplaySettingsEx()
    if rc != win32con.DISP_CHANGE_SUCCESSFUL:
        raise RuntimeError(f"final ChangeDisplaySettingsEx -> {rc}")


def main() -> int:
    displays = load_active_displays()
    if len(displays) < 2:
        print("Need at least 2 active displays; found", len(displays))
        return 1

    print("Before:")
    info = []
    primary_name = None
    for name, mode in displays:
        prim = bool(mode.DisplayFlags & win32con.CDS_SET_PRIMARY)
        # primary flag in DisplayFlags is not always set; use position (0,0)
        x, y = mode.Position_x, mode.Position_y
        w, h = mode.PelsWidth, mode.PelsHeight
        is_primary = x == 0 and y == 0
        if is_primary:
            primary_name = name
        info.append((name, x, y, w, h, is_primary))
        print(f"  {name}: pos=({x},{y}) size={w}x{h} primary={is_primary}")

    if primary_name is None:
        primary_name = info[0][0]

    primary = next(m for n, m in displays if n == primary_name)
    px, py = primary.Position_x, primary.Position_y
    pw, ph = primary.PelsWidth, primary.PelsHeight

    new_positions: dict[str, tuple[int, int, int, int]] = {}
    for name, mode in displays:
        x, y = mode.Position_x, mode.Position_y
        w, h = mode.PelsWidth, mode.PelsHeight
        if name == primary_name:
            new_positions[name] = (px, py, w, h)
        else:
            # place to the right of primary, vertically centered
            nx = px + pw if x >= px else x
            if x > px:
                nx = px + pw
            elif x < px:
                nx = x
            else:
                nx = px + pw
            ny = py + (ph - h) // 2
            new_positions[name] = (nx, ny, w, h)

    print("After (planned):")
    for name, (x, y, w, h) in new_positions.items():
        print(f"  {name}: pos=({x},{y}) size={w}x{h}")

    apply_positions(new_positions)
    print("Applied.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
