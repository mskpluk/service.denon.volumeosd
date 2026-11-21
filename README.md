# Denon Volume OSD

A Kodi service that shows the master volume of a Denon or Marantz network
receiver on screen when it changes, styled after the receiver's own volume
display. Developed against an AVR-X1400H, which overlays its display only on
signals up to 1080p; on 4K output the volume change is otherwise invisible.

## How it works

The service keeps one connection to the receiver's control port (telnet,
port 23) and reacts to the volume and mute events the receiver sends, so the
front panel knob, the IR remote, the HEOS app and other controllers all show
up. Nothing is polled, which would keep the receiver out of auto-standby.
The receiver accepts more than one control connection, so a desktop remote
can stay connected alongside.

The bar is added to the active Kodi window rather than opened as a dialog,
so it doesn't take the remote's keys while it is visible.

## Settings

- **Receiver address**: IP address or host name of the receiver.
- **Show**: above 1080p only (default), when the receiver doesn't show its
  own display, or always. The output mode is read from KScreen on KDE Plasma
  Wayland and from Kodi otherwise.
- **Volume scale**: absolute (0–98) or relative (dB).
- **Display time**: how long the bar stays on screen.

## Install

Download the zip from the releases page and use *Add-ons → Install from zip
file*.

## License

GPL-2.0-or-later; see [LICENSE.txt](LICENSE.txt).
