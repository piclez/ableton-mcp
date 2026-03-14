"""Route handlers for the HTTP bridge."""

from .devices import register as register_devices
from .system import register as register_system
from .tracks import register as register_tracks
from .transport import register as register_transport


def register_all(server):
    register_system(server)
    register_transport(server)
    register_tracks(server)
    register_devices(server)
