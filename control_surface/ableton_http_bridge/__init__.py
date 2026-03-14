"""Ableton HTTP Bridge — Control Surface for Ableton Live.

Exposes an HTTP+JSON server on localhost:8765 that provides
programmatic access to Ableton's Live Object Model (LOM).

Installed to: ~/Music/Ableton/User Library/Remote Scripts/ableton_http_bridge/
"""

import logging

from ableton.v3.control_surface import ControlSurface, ControlSurfaceSpecification, ElementsBase

from .handlers import register_all
from .http_server import BridgeServer

logger = logging.getLogger(__name__)


class Elements(ElementsBase):
    pass


class Specification(ControlSurfaceSpecification):
    elements_type = Elements
    create_mappings_function = lambda *_: {}


def create_instance(c_instance):
    """Entry point called by Ableton Live when loading this Control Surface."""
    return AbletonHttpBridge(c_instance=c_instance, specification=Specification)


class AbletonHttpBridge(ControlSurface):
    """Control Surface that runs an HTTP server for external control."""

    def setup(self):
        super().setup()
        self._http = BridgeServer(schedule_message=self.schedule_message)
        register_all(self._http)
        self._http.start()
        logger.info("AbletonHttpBridge started")

    def disconnect(self):
        self._http.stop()
        super().disconnect()
