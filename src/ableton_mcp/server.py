"""Ableton MCP server — exposes Ableton Live control as MCP tools."""

import os

from mcp.server.fastmcp import FastMCP

from ableton_mcp.client import AbletonClient

HOST = os.environ.get("ABLETON_HTTP_HOST", "localhost")
PORT = int(os.environ.get("ABLETON_HTTP_PORT", "8765"))

mcp = FastMCP("ableton")
client = AbletonClient(host=HOST, port=PORT)


# ============================================================
# GENERAL WORKFLOW FOR CONTROLLING DEVICES/INSTRUMENTS
# ============================================================
# To change a parameter on an instrument or effect:
#   1. list_tracks()                          → find track_id by name
#   2. list_devices(track_id)                 → find device_id by name/class_name
#   3. list_parameters(track_id, device_id)   → see all parameter names, current values, and [min, max] ranges
#   4. set_parameters_batch(track_id, device_id, [...])  → set multiple parameters at once
#      OR set_parameter(track_id, device_id, name, value) → set a single parameter
#
# IMPORTANT: parameter values are raw numbers in [min, max] range (NOT display strings like "2.00 kHz").
# The `display` field in list_parameters output is for human reference only — never pass it to set_parameter.
# ============================================================


# --- Transport ---


@mcp.tool()
async def get_session_info() -> dict:
    """Get current transport state.

    Returns:
        tempo: float — BPM
        signature_numerator / signature_denominator: int — time signature (e.g. 4/4)
        is_playing: bool
        is_recording: bool
        current_song_time: float — current playhead position in beats (0-based)
        song_length: float — total song length in beats
        loop: bool — whether song loop is enabled
        loop_start: float — loop start in beats
        loop_length: float — loop length in beats
        metronome: bool
    """
    return await client.get("/live/transport")


@mcp.tool()
async def get_full_state() -> dict:
    """Get a full snapshot of the entire session in one call.

    Use this at the start to understand what's in the session before doing anything.
    Returns transport info + all tracks (with volume/pan/arm/solo/mute) + currently playing clips.

    Tracks list contains: id (use as track_id), name, type ("midi"/"audio"), arm, solo, mute,
    volume {"value": float, "display": str}, pan {"value": float, "display": str}.
    Does NOT include return tracks or master — use list_returns() and get_master() for those.
    """
    return await client.get("/live/state")


@mcp.tool()
async def play() -> dict:
    """Start playback. Returns {"status": "ok"}."""
    return await client.post("/live/transport/play")


@mcp.tool()
async def stop() -> dict:
    """Stop playback. Returns {"status": "ok"}."""
    return await client.post("/live/transport/stop")


@mcp.tool()
async def record() -> dict:
    """Toggle session record mode on/off. Returns {"status": "ok", "record_mode": bool}."""
    return await client.post("/live/transport/record")


@mcp.tool()
async def set_bpm(bpm: float) -> dict:
    """Set the session tempo.

    bpm: float — typical range 60–200. Returns {"status": "ok", "tempo": float}.
    """
    return await client.post("/live/transport/bpm", {"bpm": bpm})


@mcp.tool()
async def set_loop(
    enabled: bool | None = None, start: float | None = None, length: float | None = None
) -> dict:
    """Set the song loop region. All parameters are optional — omit any you don't want to change.

    enabled: bool — turn loop on/off
    start: float — loop start in beats (NOT seconds)
    length: float — loop length in beats (NOT seconds). E.g. 16.0 = 4 bars in 4/4.
    Returns {"status": "ok", "loop": bool, "loop_start": float, "loop_length": float}.
    """
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
    """Set or toggle the metronome.

    enabled: bool — pass True/False to set explicitly, or omit to toggle.
    Returns {"status": "ok", "metronome": bool}.
    """
    data = {"enabled": enabled} if enabled is not None else {}
    return await client.post("/live/transport/metronome", data)


@mcp.tool()
async def jump_to_position(position: float) -> dict:
    """Move the playhead to a position in the timeline.

    position: float — position in beats (0-based). Beat 0 = start of song.
    E.g. 4.0 = start of bar 2 in 4/4. Returns {"status": "ok", "current_song_time": float}.
    """
    return await client.post("/live/transport/position", {"position": position})


@mcp.tool()
async def undo() -> dict:
    """Undo the last action in Ableton. Returns {"status": "ok"}."""
    return await client.post("/live/undo")


@mcp.tool()
async def redo() -> dict:
    """Redo the last undone action. Returns {"status": "ok"}."""
    return await client.post("/live/redo")


# --- Tracks ---


@mcp.tool()
async def list_tracks() -> dict:
    """List all regular tracks (MIDI and audio). Does NOT include return tracks or master.

    Returns {"tracks": [{"id": int, "name": str, "type": "midi"|"audio",
    "arm": bool, "solo": bool, "mute": bool,
    "volume": {"value": float, "display": str}, "pan": {"value": float, "display": str}}]}.
    Use the "id" field as track_id in all other track/device/clip tools.
    """
    return await client.get("/live/tracks")


@mcp.tool()
async def get_track(track_id: int) -> dict:
    """Get details for a single track including its send levels.

    track_id: int — from list_tracks().
    Returns same fields as list_tracks() entry, plus "sends": [{"index": int, "value": float, "display": str}].
    send index 0 = first return track (e.g. "A"), 1 = second, etc.
    """
    return await client.get(f"/live/tracks/{track_id}")


@mcp.tool()
async def set_track_volume(track_id: int, value: float) -> dict:
    """Set track volume.

    value: float in range 0.0–1.0. Key points: 0.0 = silence (-inf dB), 0.85 = 0 dB (unity), 1.0 = +6 dB.
    Returns {"status": "ok", "volume": {"value": float, "display": str}}.
    """
    return await client.post(f"/live/tracks/{track_id}/volume", {"value": value})


@mcp.tool()
async def set_track_pan(track_id: int, value: float) -> dict:
    """Set track pan.

    value: float in range -1.0 to 1.0. -1.0 = full left, 0.0 = center, 1.0 = full right.
    Returns {"status": "ok", "pan": {"value": float, "display": str}}.
    """
    return await client.post(f"/live/tracks/{track_id}/pan", {"value": value})


@mcp.tool()
async def set_track_arm(track_id: int, armed: bool) -> dict:
    """Arm or disarm a track for recording. Only MIDI tracks support arming.

    Returns {"status": "ok", "arm": bool}.
    """
    return await client.post(f"/live/tracks/{track_id}/arm", {"armed": armed})


@mcp.tool()
async def set_track_solo(track_id: int, solo: bool) -> dict:
    """Set track solo on/off. Returns {"status": "ok", "solo": bool}."""
    return await client.post(f"/live/tracks/{track_id}/solo", {"solo": solo})


@mcp.tool()
async def set_track_mute(track_id: int, mute: bool) -> dict:
    """Set track mute on/off. Returns {"status": "ok", "mute": bool}."""
    return await client.post(f"/live/tracks/{track_id}/mute", {"mute": mute})


@mcp.tool()
async def set_track_send(track_id: int, send_index: int, value: float) -> dict:
    """Set a send level on a track.

    send_index: int — 0-based index of the return track (0 = "A", 1 = "B", ...). Use list_returns() to see order.
    value: float in range 0.0–1.0. 0.85 = 0 dB.
    Returns {"status": "ok", "send_index": int, "value": float, "display": str}.
    """
    return await client.post(
        f"/live/tracks/{track_id}/send", {"send_index": send_index, "value": value}
    )


@mcp.tool()
async def rename_track(track_id: int, name: str) -> dict:
    """Rename a track. Returns {"status": "ok", "name": str}."""
    return await client.post(f"/live/tracks/{track_id}/name", {"name": name})


@mcp.tool()
async def select_track(track_id: int) -> dict:
    """Select a track in the Ableton GUI (highlights it). Returns {"status": "ok"}."""
    return await client.post(f"/live/tracks/{track_id}/select")


@mcp.tool()
async def duplicate_track(track_id: int) -> dict:
    """Duplicate a track. The copy is inserted immediately after the original.

    After calling, use list_tracks() to find the new track's id. Returns {"status": "ok"}.
    """
    return await client.post(f"/live/tracks/{track_id}/duplicate")


@mcp.tool()
async def stop_track(track_id: int) -> dict:
    """Stop all playing clips on a track. Returns {"status": "ok"}."""
    return await client.post(f"/live/tracks/{track_id}/stop")


@mcp.tool()
async def get_playing_clips() -> dict:
    """Get list of currently playing clips.

    Returns {"playing_clips": [{"track_id": int, "track_name": str, "clip_id": int, "clip_name": str}]}.
    """
    return await client.get("/live/playing")


@mcp.tool()
async def get_armed_tracks() -> dict:
    """Get list of tracks currently armed for recording.

    Returns {"armed_tracks": [{"id": int, "name": str}]}.
    """
    return await client.get("/live/armed")


# --- Devices ---


@mcp.tool()
async def list_devices(track_id: int) -> dict:
    """List all devices (instruments and effects) on a track.

    track_id: int — from list_tracks().
    Returns {"devices": [{"id": int, "name": str, "class_name": str, "type": str, "enabled": bool}]}.
    Use "id" as device_id in list_parameters / set_parameter / set_parameters_batch.
    "class_name" is Ableton's internal name: e.g. "InstrumentVector" = Wavetable,
    "UltraAnalog" = Analog, "Operator" = Operator, "OriginalSimpler" = Simpler,
    "MultiSampler" = Sampler, "InstrumentImpulse" = Impulse, "DrumGroupDevice" = Drum Rack.
    """
    return await client.get(f"/live/tracks/{track_id}/devices")


@mcp.tool()
async def list_parameters(track_id: int, device_id: int) -> dict:
    """List all parameters of a device with their names, current values, display strings, and ranges.

    track_id: int — from list_tracks(). device_id: int — from list_devices().
    Returns {"device": str, "class_name": str, "parameters": [
        {"name": str, "value": float, "display": str, "min": float, "max": float}
    ]}.

    IMPORTANT:
    - Use "name" exactly as returned when calling set_parameter (case-sensitive, no typos).
    - Use "value" in the range [min, max] when setting — these are raw numeric values.
    - "display" is human-readable only (e.g. "2.00 kHz") — do NOT pass it to set_parameter.
    - The first parameter is always "Device On" — use set_device_enabled() instead of set_parameter for it.

    Example parameter: {"name": "Filter Freq", "value": 2000.0, "display": "2.00 kHz", "min": 20.0, "max": 20000.0}
    To set filter to 500 Hz: set_parameter(track_id, device_id, "Filter Freq", 500.0)
    """
    return await client.get(f"/live/tracks/{track_id}/devices/{device_id}/parameters")


@mcp.tool()
async def set_parameter(track_id: int, device_id: int, name: str, value: float) -> dict:
    """Set a single device parameter by name.

    name: str — exact parameter name from list_parameters() (case-sensitive).
    value: float — numeric value within [min, max] from list_parameters(). NOT a display string.

    Workflow:
      1. list_devices(track_id) → get device_id
      2. list_parameters(track_id, device_id) → find parameter name and its min/max
      3. set_parameter(track_id, device_id, name, value)

    Example: set_parameter(0, 0, "Filter Freq", 500.0)  # sets filter to 500 Hz
    If name is not found: returns {"error": "parameter '...' not found"} — check for typos.
    On success: returns {"status": "ok", "name": str, "value": float, "display": str, "min": float, "max": float}.

    Prefer set_parameters_batch() when setting 2 or more parameters at once.
    """
    return await client.post(
        f"/live/tracks/{track_id}/devices/{device_id}/parameters/{name}",
        {"value": value},
    )


@mcp.tool()
async def set_parameters_batch(
    track_id: int, device_id: int, parameters: list[dict]
) -> dict:
    """Set multiple device parameters at once. Prefer this over multiple set_parameter calls.

    parameters: list of {"name": str, "value": float} — same rules as set_parameter.
    Each "name" must exactly match a name from list_parameters(). Each "value" must be in [min, max].

    Example:
      set_parameters_batch(0, 0, [
          {"name": "Filter Freq", "value": 500.0},
          {"name": "Resonance", "value": 0.7},
          {"name": "Osc 1 Transpose", "value": -12.0}
      ])

    Returns {"results": [{"status": "ok"|"error", "name": str, "value": float, ...}]}.
    Check each result's "status" — a typo in one name won't block the others.
    """
    return await client.post(
        f"/live/tracks/{track_id}/devices/{device_id}/parameters/batch",
        parameters,
    )


@mcp.tool()
async def set_device_enabled(track_id: int, device_id: int, enabled: bool) -> dict:
    """Enable or disable a device (bypass on/off).

    Do NOT use set_parameter for this — use this dedicated tool.
    Returns {"status": "ok", "enabled": bool}.
    """
    return await client.post(
        f"/live/tracks/{track_id}/devices/{device_id}/enabled",
        {"enabled": enabled},
    )


# --- Clips ---


@mcp.tool()
async def list_clips(track_id: int) -> dict:
    """List all clips on a track (only slots that have a clip).

    track_id: int — from list_tracks().
    Returns {"clips": [{"id": int, "has_clip": true, "name": str, "length": float,
    "looping": bool, "loop_start": float, "loop_end": float,
    "is_playing": bool, "is_recording": bool, "color": int, "color_index": int}]}.
    "id" is the slot index (0-based) — use it as clip_id in all other clip tools.
    "length" is in beats.
    """
    return await client.get(f"/live/tracks/{track_id}/clips")


@mcp.tool()
async def get_clip(track_id: int, clip_id: int) -> dict:
    """Get details for a specific clip slot.

    Returns same structure as list_clips() entry. If slot is empty: {"id": int, "has_clip": false}.
    Always check "has_clip" before using the clip data.
    """
    return await client.get(f"/live/tracks/{track_id}/clips/{clip_id}")


@mcp.tool()
async def fire_clip(track_id: int, clip_id: int) -> dict:
    """Launch (fire) a clip. Returns {"status": "ok"}."""
    return await client.post(f"/live/tracks/{track_id}/clips/{clip_id}/fire")


@mcp.tool()
async def stop_clip(track_id: int, clip_id: int) -> dict:
    """Stop a playing clip. Returns {"status": "ok"}."""
    return await client.post(f"/live/tracks/{track_id}/clips/{clip_id}/stop")


@mcp.tool()
async def create_midi_clip(track_id: int, length: float = 4.0, name: str = "") -> dict:
    """Create a new empty MIDI clip on the first empty slot of the track.

    track_id: int — must be a MIDI track (type "midi" in list_tracks()).
    length: float — clip length in beats. 4.0 = 1 bar in 4/4, 8.0 = 2 bars, 16.0 = 4 bars.
    name: str — optional name.
    Returns clip info with "id" field — that is the clip_id to use for add_notes_to_clip etc.
    If no empty slot exists: returns {"error": "no empty clip slot"}.
    """
    return await client.post(
        f"/live/tracks/{track_id}/clips/create",
        {"length": length, "name": name},
    )


@mcp.tool()
async def rename_clip(track_id: int, clip_id: int, name: str) -> dict:
    """Rename a clip. Returns {"status": "ok", "name": str}."""
    return await client.post(
        f"/live/tracks/{track_id}/clips/{clip_id}/name", {"name": name}
    )


@mcp.tool()
async def duplicate_clip(track_id: int, clip_id: int) -> dict:
    """Duplicate a clip to the next empty slot on the same track. Returns {"status": "ok"}."""
    return await client.post(f"/live/tracks/{track_id}/clips/{clip_id}/duplicate")


@mcp.tool()
async def duplicate_loop(track_id: int, clip_id: int) -> dict:
    """Double the loop content of a clip — the pattern repeats and the clip becomes twice as long.

    Returns {"status": "ok", "loop_end": float, "length": float}.
    """
    return await client.post(f"/live/tracks/{track_id}/clips/{clip_id}/duplicate_loop")


@mcp.tool()
async def get_clip_notes(track_id: int, clip_id: int) -> dict:
    """Get all MIDI notes from a clip.

    Returns {"notes": [{"pitch": int, "time": float, "duration": float, "velocity": float, "mute": bool}]}.
    pitch: MIDI note number 0–127. 60 = C4 (middle C), 69 = A4 (440 Hz).
    time: beat position from clip start (0.0 = first beat of the clip).
    duration: note length in beats. 1.0 = quarter note, 0.5 = eighth note, 0.25 = sixteenth note.
    """
    return await client.get(f"/live/tracks/{track_id}/clips/{clip_id}/notes")


@mcp.tool()
async def add_notes_to_clip(track_id: int, clip_id: int, notes: list[dict]) -> dict:
    """Add MIDI notes to a clip. Notes are ADDED to existing content — call clear_clip() first to replace.

    Each note: {"pitch": int, "time": float, "duration": float, "velocity": float, "mute": bool}
    pitch: int 0–127. 60 = C4, 62 = D4, 64 = E4, 65 = F4, 67 = G4, 69 = A4, 71 = B4, 72 = C5.
    time: float — beat position in the clip (0.0 = start). Must be >= 0 and < clip length.
    duration: float — note length in beats. 1.0 = quarter, 0.5 = eighth, 0.25 = sixteenth. Default: 0.25.
    velocity: float 0–127. Default: 100. Controls note loudness.
    mute: bool — optional, default false.

    Example — add a kick on beat 0 and a snare on beat 2 of a 4-beat clip:
      add_notes_to_clip(0, 0, [{"pitch": 36, "time": 0.0, "duration": 0.25, "velocity": 100},
                                {"pitch": 38, "time": 2.0, "duration": 0.25, "velocity": 90}])
    Returns {"status": "ok", "added": int}.
    """
    return await client.post(f"/live/tracks/{track_id}/clips/{clip_id}/notes", notes)


@mcp.tool()
async def clear_clip(track_id: int, clip_id: int) -> dict:
    """Remove all notes from a clip. The clip remains but is now empty. Returns {"status": "ok"}."""
    return await client.delete(f"/live/tracks/{track_id}/clips/{clip_id}/notes")


@mcp.tool()
async def delete_notes_by_pitch(track_id: int, clip_id: int, pitches: list[int]) -> dict:
    """Delete all notes with specific pitches from a clip.

    pitches: list of MIDI note numbers (int), e.g. [36, 38] to remove kick and snare.
    Returns {"status": "ok", "removed_pitches": [int]}.
    """
    return await client.delete(
        f"/live/tracks/{track_id}/clips/{clip_id}/notes/by_pitch",
        {"pitches": pitches},
    )


@mcp.tool()
async def delete_notes_in_range(
    track_id: int, clip_id: int, start: float, end: float
) -> dict:
    """Delete notes that start within a time range in a clip.

    start / end: float — beat positions in the clip (e.g. start=0.0, end=2.0 deletes first 2 beats).
    Returns {"status": "ok"}.
    """
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
    """Set clip loop parameters. All parameters optional — omit any you don't want to change.

    enabled: bool — turn clip looping on/off.
    start: float — loop start in beats (absolute position in clip, e.g. 0.0).
    end: float — loop end in beats (NOT length — this is the end position, e.g. 4.0 for a 4-beat loop).
    Returns {"status": "ok", "looping": bool, "loop_start": float, "loop_end": float}.
    """
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
    """Extend the clip loop end by N bars (based on current session time signature).

    bars: int — number of bars to add (default 1). In 4/4, 1 bar = 4 beats.
    Returns {"status": "ok", "loop_end": float, "length": float}.
    """
    return await client.post(
        f"/live/tracks/{track_id}/clips/{clip_id}/loop/extend", {"bars": bars}
    )


# --- Scenes ---


@mcp.tool()
async def list_scenes() -> dict:
    """List all scenes.

    Returns {"scenes": [{"id": int, "name": str, "tempo": float|null, "is_triggered": bool}]}.
    "id" is the scene_id to use in fire_scene, rename_scene, etc.
    "tempo" is null if no BPM is assigned to that scene.
    """
    return await client.get("/live/scenes")


@mcp.tool()
async def create_scene(name: str = "") -> dict:
    """Create a new scene at the end of the scene list.

    Returns {"status": "ok", "id": int, "name": str, "tempo": null, "is_triggered": false}.
    """
    data = {"name": name} if name else {}
    return await client.post("/live/scenes/create", data)


@mcp.tool()
async def fire_scene(scene_id: int) -> dict:
    """Launch all clips in a scene row. Returns {"status": "ok"}."""
    return await client.post(f"/live/scenes/{scene_id}/fire")


@mcp.tool()
async def rename_scene(scene_id: int, name: str) -> dict:
    """Rename a scene. Returns {"status": "ok", "name": str}."""
    return await client.post(f"/live/scenes/{scene_id}/name", {"name": name})


@mcp.tool()
async def duplicate_scene(scene_id: int) -> dict:
    """Duplicate a scene. Returns {"status": "ok"}."""
    return await client.post(f"/live/scenes/{scene_id}/duplicate")


@mcp.tool()
async def select_scene(scene_id: int) -> dict:
    """Select (highlight) a scene in the Ableton GUI. Returns {"status": "ok"}."""
    return await client.post(f"/live/scenes/{scene_id}/select")


@mcp.tool()
async def delete_scene(scene_id: int) -> dict:
    """Delete a scene. Cannot delete the last remaining scene (returns error).

    Returns {"status": "ok"} or {"error": "cannot delete last scene"}.
    """
    return await client.delete(f"/live/scenes/{scene_id}")


# --- Return tracks ---


@mcp.tool()
async def list_returns() -> dict:
    """List all return tracks (labeled A, B, C... in Ableton).

    Returns {"returns": [{"id": int, "name": str, "solo": bool, "mute": bool,
    "volume": {"value": float, "display": str}, "pan": {"value": float, "display": str},
    "device_count": int}]}.
    "id" is the return_id to use in set_return_volume, list_return_devices, etc.
    send_index in set_track_send corresponds to this list's order (id 0 = send A, id 1 = send B, ...).
    """
    return await client.get("/live/returns")


@mcp.tool()
async def get_return(return_id: int) -> dict:
    """Get return track details including devices.

    return_id: int — from list_returns().
    Returns same fields as list_returns() entry, plus "sends" and
    "devices": [{"id": int, "name": str, "class_name": str}].
    Use "id" from devices as device_id in list_return_device_parameters().
    """
    return await client.get(f"/live/returns/{return_id}")


@mcp.tool()
async def set_return_volume(return_id: int, value: float) -> dict:
    """Set return track volume. Same scale as set_track_volume: 0.85 = 0 dB, range 0.0–1.0.

    Returns {"status": "ok", "volume": {"value": float, "display": str}}.
    """
    return await client.post(f"/live/returns/{return_id}/volume", {"value": value})


@mcp.tool()
async def set_return_pan(return_id: int, value: float) -> dict:
    """Set return track pan. Range -1.0 (left) to 1.0 (right), 0.0 = center.

    Returns {"status": "ok", "pan": {"value": float, "display": str}}.
    """
    return await client.post(f"/live/returns/{return_id}/pan", {"value": value})


@mcp.tool()
async def list_return_devices(return_id: int) -> dict:
    """List devices on a return track.

    return_id: int — from list_returns().
    Returns {"devices": [{"id": int, "name": str, "class_name": str, "type": str, "enabled": bool}]}.
    Use "id" as device_id in list_return_device_parameters() and set_return_device_parameter().
    """
    return await client.get(f"/live/returns/{return_id}/devices")


@mcp.tool()
async def list_return_device_parameters(return_id: int, device_id: int) -> dict:
    """List parameters of a device on a return track. Same structure as list_parameters().

    Workflow: list_returns() → return_id, list_return_devices(return_id) → device_id,
    list_return_device_parameters(return_id, device_id) → parameter names and ranges.
    Returns {"device": str, "class_name": str, "parameters": [{"name", "value", "display", "min", "max"}]}.
    """
    return await client.get(f"/live/returns/{return_id}/devices/{device_id}/parameters")


@mcp.tool()
async def set_return_device_parameter(
    return_id: int, device_id: int, name: str, value: float
) -> dict:
    """Set a parameter on a return track device. Same rules as set_parameter().

    name: exact string from list_return_device_parameters(). value: numeric in [min, max].
    Returns {"status": "ok", "name": str, "value": float, "display": str, "min": float, "max": float}.
    """
    return await client.post(
        f"/live/returns/{return_id}/devices/{device_id}/parameters/{name}",
        {"value": value},
    )


# --- Master track ---


@mcp.tool()
async def get_master() -> dict:
    """Get master track info including devices.

    Returns {"name": str, "volume": {"value": float, "display": str},
    "pan": {"value": float, "display": str}, "device_count": int,
    "devices": [{"id": int, "name": str, "class_name": str}]}.
    Use "id" from devices as device_id in list_master_device_parameters() and set_master_device_parameter().
    """
    return await client.get("/live/master")


@mcp.tool()
async def set_master_volume(value: float) -> dict:
    """Set master track volume. Same scale: 0.85 = 0 dB, range 0.0–1.0.

    Returns {"status": "ok", "volume": {"value": float, "display": str}}.
    """
    return await client.post("/live/master/volume", {"value": value})


@mcp.tool()
async def list_master_devices() -> dict:
    """List devices on the master track.

    Returns {"devices": [{"id": int, "name": str, "class_name": str, "type": str, "enabled": bool}]}.
    Use "id" as device_id in list_master_device_parameters() and set_master_device_parameter().
    """
    return await client.get("/live/master/devices")


@mcp.tool()
async def list_master_device_parameters(device_id: int) -> dict:
    """List parameters of a device on the master track. Same structure as list_parameters().

    Workflow: get_master() or list_master_devices() → device_id,
    list_master_device_parameters(device_id) → parameter names and ranges.
    Returns {"device": str, "class_name": str, "parameters": [{"name", "value", "display", "min", "max"}]}.
    """
    return await client.get(f"/live/master/devices/{device_id}/parameters")


@mcp.tool()
async def set_master_device_parameter(device_id: int, name: str, value: float) -> dict:
    """Set a parameter on a master track device. Same rules as set_parameter().

    name: exact string from list_master_device_parameters(). value: numeric in [min, max].
    Returns {"status": "ok", "name": str, "value": float, "display": str, "min": float, "max": float}.
    """
    return await client.post(
        f"/live/master/devices/{device_id}/parameters/{name}",
        {"value": value},
    )


# --- Chains (racks) ---


@mcp.tool()
async def list_chains(track_id: int, device_id: int) -> dict:
    """List chains in a rack device (Instrument Rack, Audio Effect Rack, Drum Rack).

    Only works if the device is a rack. If not, returns {"error": "... does not support chains"}.
    Returns {"chains": [{"id": int, "name": str, "device_count": int,
    "devices": [{"id": int, "name": str, "class_name": str, "type": str, "enabled": bool}]}]}.
    Use chain "id" as chain_id and inner device "id" as chain_device_id in list_chain_device_parameters().
    """
    return await client.get(f"/live/tracks/{track_id}/devices/{device_id}/chains")


@mcp.tool()
async def list_chain_device_parameters(
    track_id: int, device_id: int, chain_id: int, chain_device_id: int
) -> dict:
    """List parameters of a device inside a rack chain. Same structure as list_parameters().

    Workflow:
      1. list_tracks() → track_id
      2. list_devices(track_id) → device_id (the rack)
      3. list_chains(track_id, device_id) → chain_id and chain_device_id
      4. list_chain_device_parameters(track_id, device_id, chain_id, chain_device_id)
    Returns {"device": str, "class_name": str, "parameters": [{"name", "value", "display", "min", "max"}]}.
    """
    return await client.get(
        f"/live/tracks/{track_id}/devices/{device_id}/chains/{chain_id}/devices/{chain_device_id}/parameters"
    )


@mcp.tool()
async def set_chain_device_parameter(
    track_id: int, device_id: int, chain_id: int, chain_device_id: int,
    name: str, value: float
) -> dict:
    """Set a parameter on a device inside a rack chain. Same rules as set_parameter().

    name: exact string from list_chain_device_parameters(). value: numeric in [min, max].
    Prefer set_chain_device_parameters_batch() when setting 2+ parameters.
    Returns {"status": "ok", "name": str, "value": float, "display": str, "min": float, "max": float}.
    """
    return await client.post(
        f"/live/tracks/{track_id}/devices/{device_id}/chains/{chain_id}/devices/{chain_device_id}/parameters/{name}",
        {"value": value},
    )


@mcp.tool()
async def set_chain_device_parameters_batch(
    track_id: int, device_id: int, chain_id: int, chain_device_id: int,
    parameters: list[dict]
) -> dict:
    """Set multiple parameters on a device inside a rack chain. Prefer over multiple single calls.

    parameters: list of {"name": str, "value": float} — same rules as set_chain_device_parameter().
    Returns {"results": [{"status": "ok"|"error", "name": str, "value": float, ...}]}.
    """
    return await client.post(
        f"/live/tracks/{track_id}/devices/{device_id}/chains/{chain_id}/devices/{chain_device_id}/parameters/batch",
        parameters,
    )


@mcp.tool()
async def list_drum_pads(track_id: int, device_id: int) -> dict:
    """List visible drum pads in a Drum Rack (class_name "DrumGroupDevice").

    Returns {"pads": [{"note": int, "name": str, "mute": bool, "solo": bool, "chain_count": int}]}.
    "note" is the MIDI note number that triggers this pad (e.g. 36 = C1 = typically kick).
    Shows the 16 visible pads only (out of 128 possible). Use list_chains() to access
    the devices inside each pad's chain.
    """
    return await client.get(f"/live/tracks/{track_id}/devices/{device_id}/drum_pads")


# --- Track creation ---


@mcp.tool()
async def create_midi_track(index: int = -1) -> dict:
    """Create a new empty MIDI track.

    index: int — position to insert (0-based). -1 adds at the end (default).
    Returns {"status": "ok", "track_count": int}. After creating, call list_tracks() to find the new track's id.
    """
    return await client.post("/live/tracks/create_midi", {"index": index})


@mcp.tool()
async def create_audio_track(index: int = -1) -> dict:
    """Create a new empty audio track.

    index: int — position to insert (0-based). -1 adds at the end (default).
    Returns {"status": "ok", "track_count": int}. After creating, call list_tracks() to find the new track's id.
    """
    return await client.post("/live/tracks/create_audio", {"index": index})


@mcp.tool()
async def delete_track(track_id: int) -> dict:
    """Delete a track. WARNING: this is irreversible (use undo() if needed).

    After deleting, track_ids of remaining tracks may shift — call list_tracks() to refresh.
    Returns {"status": "ok", "track_count": int}.
    """
    return await client.delete(f"/live/tracks/{track_id}")


# --- Clip color ---


@mcp.tool()
async def set_clip_color(track_id: int, clip_id: int, color_index: int) -> dict:
    """Set a clip's color by Ableton color index (0–69).

    Returns {"status": "ok", "color": int, "color_index": int}.
    """
    return await client.post(
        f"/live/tracks/{track_id}/clips/{clip_id}/color",
        {"color_index": color_index},
    )


def main():
    mcp.run(transport="stdio")
