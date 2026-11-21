"""Volume bar drawn over whatever Kodi shows, styled after the receiver's own.

The controls are added to the active window instead of opening a dialog:
Python dialogs are modal and would take the remote's keys while visible.
Coordinates are in the skin's 1920x1080 space, so the bar keeps its size and
place whatever the output resolution.
"""

import os

import xbmcaddon
import xbmcgui

MEDIA = os.path.join(xbmcaddon.Addon().getAddonInfo("path"), "resources", "media")
WHITE = os.path.join(MEDIA, "white.png")

# Layout of the AVR-X1400H volume display, measured on screen (skin pixels, 1920x1080)
BAND_X, BAND_Y, BAND_W, BAND_H = 312, 940, 1090, 86
BAR_X, BAR_Y, BAR_W, BAR_H = 362, 972, 720, 22
BORDER = 2
NUMBER_X, NUMBER_W = 1150, 160
BAND = "F5020204"
OUTLINE = "FFE6F0FF"
FILL = "FF78B6FE"
TEXT = "FFF0F2FF"
FONT = "Mono26"


def volume_text(volume, muted, scale_db):
    if muted:
        return "MUTING"
    if scale_db:
        return "---.-dB" if volume == 0 else f"{volume - 80:.1f}dB"
    return f"{volume:.1f}"


class Overlay:
    def __init__(self):
        self.window = None
        self.window_id = None
        self.controls = []

    def _create(self):
        inner_x, inner_y = BAR_X + BORDER, BAR_Y + BORDER
        inner_w, inner_h = BAR_W - 2 * BORDER, BAR_H - 2 * BORDER
        self.band = xbmcgui.ControlImage(BAND_X, BAND_Y, BAND_W, BAND_H, WHITE, colorDiffuse=BAND)
        self.outline = xbmcgui.ControlImage(BAR_X, BAR_Y, BAR_W, BAR_H, WHITE, colorDiffuse=OUTLINE)
        self.inner = xbmcgui.ControlImage(inner_x, inner_y, inner_w, inner_h, WHITE,
                                          colorDiffuse=BAND)
        self.fill = xbmcgui.ControlImage(inner_x, inner_y, 1, inner_h, WHITE, colorDiffuse=FILL)
        # right and vertically centred
        self.value = xbmcgui.ControlLabel(NUMBER_X, BAND_Y, NUMBER_W, BAND_H, "", font=FONT,
                                          textColor=TEXT, alignment=0x00000001 | 0x00000004)
        self.inner_w = inner_w
        self.controls = [self.band, self.outline, self.inner, self.fill, self.value]

    def show(self, volume, muted, maximum, scale_db):
        window_id = xbmcgui.getCurrentWindowId()
        if self.window is not None and self.window_id != window_id:
            self.hide()
        if self.window is None:
            self._create()
            self.window = xbmcgui.Window(window_id)
            self.window_id = window_id
            self.window.addControls(self.controls)

        # Wide letter spacing, as the receiver's font
        self.value.setLabel(" ".join(volume_text(volume, muted, scale_db)))
        # The receiver fills the bar up to its configured maximum volume.
        top = maximum or 98
        width = 0 if muted else int(self.inner_w * min(volume, top) / top)
        self.fill.setWidth(max(width, 1))
        self.fill.setVisible(width > 0)

    def hide(self):
        if self.window is None:
            return
        try:
            self.window.removeControls(self.controls)
        except RuntimeError:
            pass
        self.window = None
        self.window_id = None
        self.controls = []
