"""HTTP server running inside Ableton's Python environment.

Uses only Python stdlib (no pip packages available in Ableton).
Runs in a daemon thread to avoid blocking Ableton's main thread.
"""

import json
import logging
import os
import queue
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import unquote

logger = logging.getLogger(__name__)

# Override with ABLETON_HTTP_PORT to run alongside another control surface that
# also binds 8765.
DEFAULT_PORT = int(os.environ.get("ABLETON_HTTP_PORT", "8765"))


class RequestHandler(BaseHTTPRequestHandler):
    """Handles HTTP requests and dispatches to registered route handlers."""

    def do_GET(self):
        self._handle("GET")

    def do_POST(self):
        self._handle("POST")

    def do_DELETE(self):
        self._handle("DELETE")

    def _handle(self, method):
        # Unquote per segment: parameter names contain spaces ("1 Filter Type A")
        # and arrive percent-encoded, which would never match the route table.
        raw = self.path.split("?")[0].rstrip("/")
        path = "/".join(unquote(seg) for seg in raw.split("/"))
        body = self._read_body()

        handler, params = self.server.router.match(method, path)
        if handler is None:
            self._respond(404, {"error": f"Not found: {method} {path}"})
            return

        try:
            result = self.server.run_on_main_thread(handler, body=body, **params)
            self._respond(200, result)
        except Exception as e:
            logger.exception("Handler error: %s %s", method, path)
            self._respond(500, {"error": str(e)})

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return None
        raw = self.rfile.read(length)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    def _respond(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        logger.debug(format, *args)


class Router:
    """Simple path router with support for {param} placeholders."""

    def __init__(self):
        self._routes = []

    def add(self, method, pattern, handler):
        parts = pattern.rstrip("/").split("/")
        self._routes.append((method, parts, handler))

    def match(self, method, path):
        path_parts = path.split("/")
        for route_method, route_parts, handler in self._routes:
            if route_method != method:
                continue
            if len(route_parts) != len(path_parts):
                continue
            params = {}
            matched = True
            for rp, pp in zip(route_parts, path_parts):
                if rp.startswith("{") and rp.endswith("}"):
                    param_name = rp[1:-1]
                    try:
                        params[param_name] = int(pp)
                    except ValueError:
                        params[param_name] = pp
                elif rp != pp:
                    matched = False
                    break
            if matched:
                return handler, params
        return None, {}


class MainThreadDispatcher:
    """Dispatches callables from HTTP thread to Ableton's main thread.

    HTTP handler puts (fn, kwargs, result_event, result_holder) into a queue.
    The main thread polls the queue via schedule_message and executes them.
    """

    POLL_INTERVAL_MS = 10

    def __init__(self, schedule_message):
        self._queue = queue.Queue()
        self._schedule = schedule_message
        self._polling = False

    def submit(self, fn, **kwargs):
        result_holder = {}
        event = threading.Event()
        self._queue.put((fn, kwargs, event, result_holder))
        self._ensure_polling()
        if not event.wait(timeout=10.0):
            logger.warning("Timeout waiting for %s on main thread", fn.__name__)
        if "error" in result_holder:
            raise result_holder["error"]
        return result_holder.get("result")

    def _ensure_polling(self):
        if not self._polling:
            self._polling = True
            self._schedule(self.POLL_INTERVAL_MS, self._poll)

    def _poll(self):
        try:
            while not self._queue.empty():
                fn, kwargs, event, holder = self._queue.get_nowait()
                try:
                    holder["result"] = fn(**kwargs)
                except Exception as e:
                    logger.exception("Handler error in %s", fn.__name__)
                    holder["error"] = e
                finally:
                    event.set()
        finally:
            if not self._queue.empty():
                self._schedule(self.POLL_INTERVAL_MS, self._poll)
            else:
                self._polling = False


class BridgeServer:
    """HTTP server that runs in a daemon thread inside Ableton."""

    def __init__(self, schedule_message, port=DEFAULT_PORT):
        self.port = port
        self.router = Router()
        self._dispatcher = MainThreadDispatcher(schedule_message)
        self._server = None
        self._thread = None

    def route(self, method, pattern):
        """Decorator to register a route handler."""
        def decorator(fn):
            self.router.add(method, pattern, fn)
            return fn
        return decorator

    def run_on_main_thread(self, fn, **kwargs):
        return self._dispatcher.submit(fn, **kwargs)

    def start(self):
        self._server = HTTPServer(("127.0.0.1", self.port), RequestHandler)
        self._server.router = self.router
        self._server.run_on_main_thread = self.run_on_main_thread
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        logger.info("HTTP bridge listening on 127.0.0.1:%d", self.port)

    def stop(self):
        if self._server:
            self._server.shutdown()
            self._server.server_close()
            logger.info("HTTP bridge stopped")
