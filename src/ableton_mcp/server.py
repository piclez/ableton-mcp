"""Ableton MCP server — exposes Ableton Live control as MCP tools."""

import os

from mcp.server.fastmcp import FastMCP

from ableton_mcp.client import AbletonClient

HOST = os.environ.get("ABLETON_HTTP_HOST", "localhost")
PORT = int(os.environ.get("ABLETON_HTTP_PORT", "8765"))

mcp = FastMCP("ableton")
client = AbletonClient(host=HOST, port=PORT)


# --- Transport ---


@mcp.tool()
async def get_session_info() -> dict:
    """Get current session info: BPM, transport state, is_playing, is_recording."""
    return await client.get("/live/transport")


@mcp.tool()
async def play() -> dict:
    """Start playback."""
    return await client.post("/live/transport/play")


@mcp.tool()
async def stop() -> dict:
    """Stop playback."""
    return await client.post("/live/transport/stop")


@mcp.tool()
async def set_bpm(bpm: float) -> dict:
    """Set the session tempo in BPM."""
    return await client.post("/live/transport/bpm", {"bpm": bpm})


# --- Tracks ---


@mcp.tool()
async def list_tracks() -> dict:
    """List all tracks with names, types, volume, pan, arm, solo, mute."""
    return await client.get("/live/tracks")


@mcp.tool()
async def set_track_volume(track_id: int, value: float) -> dict:
    """Set track volume (0.0 to 1.0)."""
    return await client.post(f"/live/tracks/{track_id}/volume", {"value": value})


@mcp.tool()
async def set_track_arm(track_id: int, armed: bool) -> dict:
    """Arm or disarm a track for recording."""
    return await client.post(f"/live/tracks/{track_id}/arm", {"armed": armed})


# --- Devices ---


@mcp.tool()
async def list_devices(track_id: int) -> dict:
    """List all devices on a track."""
    return await client.get(f"/live/tracks/{track_id}/devices")


@mcp.tool()
async def list_parameters(track_id: int, device_id: int) -> dict:
    """List all parameters of a device with name, min, max, value."""
    return await client.get(f"/live/tracks/{track_id}/devices/{device_id}/parameters")


@mcp.tool()
async def set_parameter(track_id: int, device_id: int, name: str, value: float) -> dict:
    """Set a device parameter by name."""
    return await client.post(
        f"/live/tracks/{track_id}/devices/{device_id}/parameters/{name}",
        {"value": value},
    )


@mcp.tool()
async def set_parameters_batch(
    track_id: int, device_id: int, parameters: list[dict]
) -> dict:
    """Set multiple device parameters at once. Each item: {"name": "...", "value": ...}."""
    return await client.post(
        f"/live/tracks/{track_id}/devices/{device_id}/parameters/batch",
        parameters,
    )


# --- Clips ---


@mcp.tool()
async def list_clips(track_id: int) -> dict:
    """List all clips on a track."""
    return await client.get(f"/live/tracks/{track_id}/clips")


@mcp.tool()
async def fire_clip(track_id: int, clip_id: int) -> dict:
    """Fire (launch) a clip."""
    return await client.post(f"/live/tracks/{track_id}/clips/{clip_id}/fire")


@mcp.tool()
async def create_midi_clip(track_id: int, length: float = 4.0, name: str = "") -> dict:
    """Create a new MIDI clip on the track."""
    return await client.post(
        f"/live/tracks/{track_id}/clips/create",
        {"length": length, "name": name},
    )


@mcp.tool()
async def add_notes_to_clip(track_id: int, clip_id: int, notes: list[dict]) -> dict:
    """Add MIDI notes to a clip. Each note: {pitch, time, duration, velocity}."""
    return await client.post(f"/live/tracks/{track_id}/clips/{clip_id}/notes", notes)


@mcp.tool()
async def clear_clip(track_id: int, clip_id: int) -> dict:
    """Remove all notes from a clip."""
    return await client.delete(f"/live/tracks/{track_id}/clips/{clip_id}/notes")


# --- Scenes ---


@mcp.tool()
async def list_scenes() -> dict:
    """List all scenes with names."""
    return await client.get("/live/scenes")


@mcp.tool()
async def fire_scene(scene_id: int) -> dict:
    """Fire (launch) a scene."""
    return await client.post(f"/live/scenes/{scene_id}/fire")


# --- Undo/Redo ---


@mcp.tool()
async def undo() -> dict:
    """Undo the last action in Ableton."""
    return await client.post("/live/undo")


@mcp.tool()
async def redo() -> dict:
    """Redo the last undone action."""
    return await client.post("/live/redo")


def main():
    mcp.run(transport="stdio")
