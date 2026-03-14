"""Route handlers for the HTTP bridge."""

from .clips import register as register_clips
from .devices import register as register_devices
from .scenes import register as register_scenes
from .system import register as register_system
from .tracks import register as register_tracks
from .transport import register as register_transport


def register_all(server):
    register_system(server)
    register_transport(server)
    register_tracks(server)
    register_devices(server)
    register_clips(server)
    register_scenes(server)
