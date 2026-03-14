"""Ableton HTTP Bridge — Control Surface for Ableton Live.

Exposes an HTTP+JSON server on localhost:8765 that provides
programmatic access to Ableton's Live Object Model (LOM).

Installed to: ~/Music/Ableton/User Library/Remote Scripts/ableton_http_bridge/
"""

from ableton.v3.control_surface import ControlSurface


def create_instance(c_instance):
    """Entry point called by Ableton Live when loading this Control Surface."""
    return AbletonHttpBridge(c_instance=c_instance)


class AbletonHttpBridge(ControlSurface):
    """Control Surface that runs an HTTP server for external control."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # HTTP server will be started here in Etap 1
