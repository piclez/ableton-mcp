"""Route handlers for the HTTP bridge."""

from .system import register as register_system
from .transport import register as register_transport


def register_all(server):
    register_system(server)
    register_transport(server)
