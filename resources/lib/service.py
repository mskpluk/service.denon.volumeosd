"""Shows the receiver's volume on screen when it changes."""

import queue
import time

import xbmc
import xbmcaddon

from resources.lib.display import receiver_osd_hidden
from resources.lib.overlay import Overlay
from resources.lib.receiver import Receiver, log


class Service(xbmc.Monitor):
    def __init__(self):
        super().__init__()
        self.events = queue.Queue()
        self.receiver = None
        self.overlay = Overlay()
        self.hide_at = 0.0
        self.load_settings()

    def load_settings(self):
        addon = xbmcaddon.Addon()
        self.host = addon.getSetting("host").strip()
        self.duration = addon.getSettingNumber("duration")
        self.scale_db = addon.getSettingInt("scale") == 1
        self.always = addon.getSettingInt("show") == 1

    def onSettingsChanged(self):
        host = self.host
        self.load_settings()
        if host != self.host:
            self.restart_receiver()

    def restart_receiver(self):
        if self.receiver:
            self.receiver.stop()
            self.receiver = None
        if not self.host:
            log("no receiver address set")
            return
        self.receiver = Receiver(self.host, lambda *state: self.events.put(state), self)
        self.receiver.start()

    def run(self):
        log("started")
        self.restart_receiver()
        while not self.abortRequested():
            try:
                volume, muted, maximum = self.events.get(timeout=0.1)
                # The receiver shows its own display up to 1080p.
                if self.always or receiver_osd_hidden():
                    self.overlay.show(volume, muted, maximum, self.scale_db)
                    self.hide_at = time.monotonic() + self.duration
                else:
                    self.overlay.hide()
                    self.hide_at = 0.0
            except queue.Empty:
                pass
            if self.hide_at and time.monotonic() >= self.hide_at:
                self.overlay.hide()
                self.hide_at = 0.0
        self.overlay.hide()
        if self.receiver:
            self.receiver.stop()
