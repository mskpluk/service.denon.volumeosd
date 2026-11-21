"""Whether the receiver can overlay its own volume display.

The AVR-X1400H draws it only on signals up to 1080p. The output mode is read
from KScreen on KDE Plasma, as Kodi doesn't always know a mode set outside it,
and from Kodi otherwise.
"""

import json
import os
import shutil
import subprocess
import time

import xbmc

FHD_HEIGHT = 1080
CACHE_SECONDS = 2.0

_cache = (0.0, None)


def _kscreen_height():
    if not os.environ.get("WAYLAND_DISPLAY") or not shutil.which("kscreen-doctor"):
        return None
    try:
        out = subprocess.run(["kscreen-doctor", "-j"], capture_output=True, text=True,
                             timeout=3).stdout
        heights = []
        for output in json.loads(out).get("outputs", []):
            if not output.get("enabled"):
                continue
            for mode in output.get("modes", []):
                if str(mode.get("id")) == str(output.get("currentModeId")):
                    heights.append(mode["size"]["height"])
        return max(heights) if heights else None
    except (OSError, subprocess.TimeoutExpired, ValueError, KeyError):
        return None


def _kodi_height():
    try:
        return int(xbmc.getInfoLabel("System.ScreenHeight"))
    except ValueError:
        return None


def output_height():
    global _cache
    now = time.monotonic()
    if now - _cache[0] < CACHE_SECONDS and _cache[1]:
        return _cache[1]
    height = _kscreen_height() or _kodi_height()
    _cache = (now, height)
    return height


def receiver_osd_hidden():
    height = output_height()
    return height is None or height > FHD_HEIGHT
