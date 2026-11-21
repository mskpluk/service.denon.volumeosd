"""Control connection to a Denon or Marantz receiver (telnet, port 23).

The receiver announces every change on this connection, whatever caused it:
the front panel, the IR remote, the HEOS app or another controller. Nothing
is polled, a periodic query would keep the receiver out of auto-standby.
"""

import socket
import threading

import xbmc

PORT = 23
RECONNECT_DELAY = 5


def log(msg, level=xbmc.LOGINFO):
    xbmc.log(f"[service.denon.volumeosd] {msg}", level)


def parse_volume(value):
    """'56' -> 56.0, '565' -> 56.5 (three digits are a half step)."""
    if not value.isdigit():
        return None
    if len(value) == 3:
        return int(value[:2]) + 0.5
    return float(int(value))


class Receiver(threading.Thread):
    """Reads the event stream and calls on_volume(volume, muted, maximum, initial)."""

    def __init__(self, host, on_change, monitor):
        super().__init__(daemon=True)
        self.host = host
        self.on_change = on_change
        self.monitor = monitor
        self.volume = None
        self.maximum = None
        self.muted = False
        self._sock = None
        self._initial = True
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()
        sock = self._sock
        if sock:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

    def run(self):
        while not self._stop.is_set() and not self.monitor.abortRequested():
            try:
                self._session()
            except OSError as e:
                log(f"{self.host}: {e}", xbmc.LOGDEBUG)
            self._sock = None
            if self._stop.wait(RECONNECT_DELAY):
                break

    def _session(self):
        sock = socket.create_connection((self.host, PORT), timeout=5)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        for opt, val in (("TCP_KEEPIDLE", 30), ("TCP_KEEPINTVL", 10), ("TCP_KEEPCNT", 3)):
            if hasattr(socket, opt):
                sock.setsockopt(socket.IPPROTO_TCP, getattr(socket, opt), val)
        sock.settimeout(None)
        self._sock = sock
        log(f"connected to {self.host}")

        # Current state once, without showing it.
        self._initial = True
        sock.sendall(b"MV?\r")
        sock.sendall(b"MU?\r")

        buf = b""
        while not self._stop.is_set():
            data = sock.recv(4096)
            if not data:
                raise OSError("connection closed")
            buf += data
            *lines, buf = buf.split(b"\r")
            for line in lines:
                self._handle(line.decode("ascii", "replace").strip())

    def _handle(self, line):
        changed = False
        if line.startswith("MVMAX"):
            self.maximum = parse_volume(line[5:].strip())
        elif line.startswith("MV"):
            volume = parse_volume(line[2:])
            if volume is not None:
                changed = volume != self.volume
                self.volume = volume
        elif line in ("MUON", "MUOFF"):
            muted = line == "MUON"
            changed = muted != self.muted
            self.muted = muted
        else:
            return

        if self.volume is None:
            return
        if self._initial:
            # The answer to MU?, asked last, completes the initial state.
            if line in ("MUON", "MUOFF"):
                self._initial = False
            return
        if changed:
            self.on_change(self.volume, self.muted, self.maximum)
