"""Tests for the Control Surface HTTP router (no Ableton dependency)."""

import importlib.util
import os

# Import http_server directly to avoid ableton_http_bridge/__init__.py
# which requires the Ableton runtime (ableton.v3).
_spec = importlib.util.spec_from_file_location(
    "http_server",
    os.path.join(os.path.dirname(__file__), "..", "control_surface", "ableton_http_bridge", "http_server.py"),
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
Router = _mod.Router


def make_router(*routes):
    """Helper: create a Router with given (method, pattern, handler) tuples."""
    r = Router()
    for method, pattern, handler in routes:
        r.add(method, pattern, handler)
    return r


def dummy():
    pass


class TestRouterBasicMatching:
    def test_exact_match(self):
        r = make_router(("GET", "/live/ping", dummy))
        handler, params = r.match("GET", "/live/ping")
        assert handler is dummy
        assert params == {}

    def test_method_mismatch(self):
        r = make_router(("GET", "/live/ping", dummy))
        handler, params = r.match("POST", "/live/ping")
        assert handler is None

    def test_no_match(self):
        r = make_router(("GET", "/live/ping", dummy))
        handler, params = r.match("GET", "/live/pong")
        assert handler is None

    def test_trailing_slash_stripped_on_add(self):
        r = make_router(("GET", "/live/ping/", dummy))
        handler, _ = r.match("GET", "/live/ping")
        assert handler is dummy

    def test_first_match_wins(self):
        def first():
            return "first"

        def second():
            return "second"

        r = make_router(("GET", "/live/thing", first), ("GET", "/live/thing", second))
        handler, _ = r.match("GET", "/live/thing")
        assert handler is first


class TestRouterPathParams:
    def test_integer_param(self):
        r = make_router(("GET", "/live/tracks/{track_id}", dummy))
        handler, params = r.match("GET", "/live/tracks/5")
        assert handler is dummy
        assert params == {"track_id": 5}

    def test_string_param_fallback(self):
        r = make_router(("POST", "/live/tracks/{track_id}/arrangement_clips/{start_time}", dummy))
        handler, params = r.match("POST", "/live/tracks/0/arrangement_clips/8.0")
        assert handler is dummy
        assert params["track_id"] == 0
        assert params["start_time"] == "8.0"

    def test_multiple_params(self):
        r = make_router(("GET", "/live/tracks/{track_id}/devices/{device_id}/parameters", dummy))
        handler, params = r.match("GET", "/live/tracks/2/devices/3/parameters")
        assert handler is dummy
        assert params == {"track_id": 2, "device_id": 3}

    def test_wrong_length_no_match(self):
        r = make_router(("GET", "/live/tracks/{track_id}", dummy))
        handler, _ = r.match("GET", "/live/tracks/5/clips")
        assert handler is None

    def test_delete_method(self):
        r = make_router(("DELETE", "/live/tracks/{track_id}", dummy))
        handler, params = r.match("DELETE", "/live/tracks/7")
        assert handler is dummy
        assert params == {"track_id": 7}
