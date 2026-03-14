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
    """Get current session info: BPM, transport state, is_playing, is_recording, loop, metronome."""
    return await client.get("/live/transport")


@mcp.tool()
async def get_full_state() -> dict:
    """Get full session snapshot: transport + all tracks (with volume/pan/arm) + playing clips."""
    return await client.get("/live/state")


@mcp.tool()
async def play() -> dict:
    """Start playback."""
    return await client.post("/live/transport/play")


@mcp.tool()
async def stop() -> dict:
    """Stop playback."""
    return await client.post("/live/transport/stop")


@mcp.tool()
async def record() -> dict:
    """Toggle recording mode."""
    return await client.post("/live/transport/record")


@mcp.tool()
async def set_bpm(bpm: float) -> dict:
    """Set the session tempo in BPM."""
    return await client.post("/live/transport/bpm", {"bpm": bpm})


@mcp.tool()
async def set_loop(
    enabled: bool | None = None, start: float | None = None, length: float | None = None
) -> dict:
    """Set the song loop region. All parameters optional."""
    data = {}
    if enabled is not None:
        data["enabled"] = enabled
    if start is not None:
        data["start"] = start
    if length is not None:
        data["length"] = length
    return await client.post("/live/transport/loop", data)


@mcp.tool()
async def set_metronome(enabled: bool | None = None) -> dict:
    """Toggle or set the metronome."""
    data = {"enabled": enabled} if enabled is not None else {}
    return await client.post("/live/transport/metronome", data)


@mcp.tool()
async def jump_to_position(position: float) -> dict:
    """Jump to a position in the timeline (in beats)."""
    return await client.post("/live/transport/position", {"position": position})


@mcp.tool()
async def undo() -> dict:
    """Undo the last action in Ableton."""
    return await client.post("/live/undo")


@mcp.tool()
async def redo() -> dict:
    """Redo the last undone action."""
    return await client.post("/live/redo")


# --- Tracks ---


@mcp.tool()
async def list_tracks() -> dict:
    """List all tracks with names, types, volume (with dB display), pan, arm, solo, mute."""
    return await client.get("/live/tracks")


@mcp.tool()
async def get_track(track_id: int) -> dict:
    """Get track details including sends."""
    return await client.get(f"/live/tracks/{track_id}")


@mcp.tool()
async def set_track_volume(track_id: int, value: float) -> dict:
    """Set track volume (0.0='-inf dB', 0.85='0 dB', 1.0='+6 dB')."""
    return await client.post(f"/live/tracks/{track_id}/volume", {"value": value})


@mcp.tool()
async def set_track_pan(track_id: int, value: float) -> dict:
    """Set track pan (-1.0=left, 0.0=center, 1.0=right)."""
    return await client.post(f"/live/tracks/{track_id}/pan", {"value": value})


@mcp.tool()
async def set_track_arm(track_id: int, armed: bool) -> dict:
    """Arm or disarm a track for recording."""
    return await client.post(f"/live/tracks/{track_id}/arm", {"armed": armed})


@mcp.tool()
async def set_track_solo(track_id: int, solo: bool) -> dict:
    """Set track solo on/off."""
    return await client.post(f"/live/tracks/{track_id}/solo", {"solo": solo})


@mcp.tool()
async def set_track_mute(track_id: int, mute: bool) -> dict:
    """Set track mute on/off."""
    return await client.post(f"/live/tracks/{track_id}/mute", {"mute": mute})


@mcp.tool()
async def set_track_send(track_id: int, send_index: int, value: float) -> dict:
    """Set a send level on a track."""
    return await client.post(
        f"/live/tracks/{track_id}/send", {"send_index": send_index, "value": value}
    )


@mcp.tool()
async def rename_track(track_id: int, name: str) -> dict:
    """Rename a track."""
    return await client.post(f"/live/tracks/{track_id}/name", {"name": name})


@mcp.tool()
async def select_track(track_id: int) -> dict:
    """Select a track in the Ableton GUI."""
    return await client.post(f"/live/tracks/{track_id}/select")


@mcp.tool()
async def duplicate_track(track_id: int) -> dict:
    """Duplicate a track with all its contents."""
    return await client.post(f"/live/tracks/{track_id}/duplicate")


@mcp.tool()
async def stop_track(track_id: int) -> dict:
    """Stop all clips on a track."""
    return await client.post(f"/live/tracks/{track_id}/stop")


@mcp.tool()
async def get_playing_clips() -> dict:
    """Get list of currently playing clips."""
    return await client.get("/live/playing")


@mcp.tool()
async def get_armed_tracks() -> dict:
    """Get list of armed tracks."""
    return await client.get("/live/armed")


# --- Devices ---


@mcp.tool()
async def list_devices(track_id: int) -> dict:
    """List all devices on a track with name, class_name, type, enabled."""
    return await client.get(f"/live/tracks/{track_id}/devices")


@mcp.tool()
async def list_parameters(track_id: int, device_id: int) -> dict:
    """List all parameters of a device with name, value, display, min, max."""
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


@mcp.tool()
async def set_device_enabled(track_id: int, device_id: int, enabled: bool) -> dict:
    """Enable or disable a device."""
    return await client.post(
        f"/live/tracks/{track_id}/devices/{device_id}/enabled",
        {"enabled": enabled},
    )


# --- Clips ---


@mcp.tool()
async def list_clips(track_id: int) -> dict:
    """List all clips on a track with name, length, loop info, playing state."""
    return await client.get(f"/live/tracks/{track_id}/clips")


@mcp.tool()
async def get_clip(track_id: int, clip_id: int) -> dict:
    """Get clip details."""
    return await client.get(f"/live/tracks/{track_id}/clips/{clip_id}")


@mcp.tool()
async def fire_clip(track_id: int, clip_id: int) -> dict:
    """Fire (launch) a clip."""
    return await client.post(f"/live/tracks/{track_id}/clips/{clip_id}/fire")


@mcp.tool()
async def stop_clip(track_id: int, clip_id: int) -> dict:
    """Stop a clip."""
    return await client.post(f"/live/tracks/{track_id}/clips/{clip_id}/stop")


@mcp.tool()
async def create_midi_clip(track_id: int, length: float = 4.0, name: str = "") -> dict:
    """Create a new MIDI clip on the first empty slot."""
    return await client.post(
        f"/live/tracks/{track_id}/clips/create",
        {"length": length, "name": name},
    )


@mcp.tool()
async def rename_clip(track_id: int, clip_id: int, name: str) -> dict:
    """Rename a clip."""
    return await client.post(
        f"/live/tracks/{track_id}/clips/{clip_id}/name", {"name": name}
    )


@mcp.tool()
async def duplicate_clip(track_id: int, clip_id: int) -> dict:
    """Duplicate a clip to the next empty slot."""
    return await client.post(f"/live/tracks/{track_id}/clips/{clip_id}/duplicate")


@mcp.tool()
async def duplicate_loop(track_id: int, clip_id: int) -> dict:
    """Duplicate the loop content of a clip (doubles the pattern)."""
    return await client.post(f"/live/tracks/{track_id}/clips/{clip_id}/duplicate_loop")


@mcp.tool()
async def get_clip_notes(track_id: int, clip_id: int) -> dict:
    """Get all MIDI notes from a clip: [{pitch, time, duration, velocity, mute}]."""
    return await client.get(f"/live/tracks/{track_id}/clips/{clip_id}/notes")


@mcp.tool()
async def add_notes_to_clip(track_id: int, clip_id: int, notes: list[dict]) -> dict:
    """Add MIDI notes to a clip. Each note: {pitch, time, duration, velocity}."""
    return await client.post(f"/live/tracks/{track_id}/clips/{clip_id}/notes", notes)


@mcp.tool()
async def clear_clip(track_id: int, clip_id: int) -> dict:
    """Remove all notes from a clip."""
    return await client.delete(f"/live/tracks/{track_id}/clips/{clip_id}/notes")


@mcp.tool()
async def delete_notes_by_pitch(track_id: int, clip_id: int, pitches: list[int]) -> dict:
    """Delete notes with specific pitches from a clip."""
    return await client.delete(
        f"/live/tracks/{track_id}/clips/{clip_id}/notes/by_pitch",
        {"pitches": pitches},
    )


@mcp.tool()
async def delete_notes_in_range(
    track_id: int, clip_id: int, start: float, end: float
) -> dict:
    """Delete notes in a time range from a clip."""
    return await client.delete(
        f"/live/tracks/{track_id}/clips/{clip_id}/notes/in_range",
        {"start": start, "end": end},
    )


@mcp.tool()
async def set_clip_loop(
    track_id: int,
    clip_id: int,
    enabled: bool | None = None,
    start: float | None = None,
    end: float | None = None,
) -> dict:
    """Set clip loop parameters."""
    data = {}
    if enabled is not None:
        data["enabled"] = enabled
    if start is not None:
        data["start"] = start
    if end is not None:
        data["end"] = end
    return await client.post(f"/live/tracks/{track_id}/clips/{clip_id}/loop", data)


@mcp.tool()
async def extend_clip_loop(track_id: int, clip_id: int, bars: int = 1) -> dict:
    """Extend the clip loop by N bars."""
    return await client.post(
        f"/live/tracks/{track_id}/clips/{clip_id}/loop/extend", {"bars": bars}
    )


# --- Scenes ---


@mcp.tool()
async def list_scenes() -> dict:
    """List all scenes with names."""
    return await client.get("/live/scenes")


@mcp.tool()
async def create_scene(name: str = "") -> dict:
    """Create a new scene at the end."""
    data = {"name": name} if name else {}
    return await client.post("/live/scenes/create", data)


@mcp.tool()
async def fire_scene(scene_id: int) -> dict:
    """Fire (launch) a scene."""
    return await client.post(f"/live/scenes/{scene_id}/fire")


@mcp.tool()
async def rename_scene(scene_id: int, name: str) -> dict:
    """Rename a scene."""
    return await client.post(f"/live/scenes/{scene_id}/name", {"name": name})


@mcp.tool()
async def duplicate_scene(scene_id: int) -> dict:
    """Duplicate a scene."""
    return await client.post(f"/live/scenes/{scene_id}/duplicate")


@mcp.tool()
async def select_scene(scene_id: int) -> dict:
    """Select a scene in the Ableton GUI."""
    return await client.post(f"/live/scenes/{scene_id}/select")


@mcp.tool()
async def delete_scene(scene_id: int) -> dict:
    """Delete a scene."""
    return await client.delete(f"/live/scenes/{scene_id}")


def main():
    mcp.run(transport="stdio")
