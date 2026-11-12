"""Arrangement View endpoints: clips CRUD, move/resize/loop, clip envelopes."""

from ableton.v3.live import util


def _get_track(track_id):
    tracks = list(util.song().tracks)
    if track_id < 0 or track_id >= len(tracks):
        return None
    return tracks[track_id]


def _get_arrangement_clip(track_id, start_time):
    track = _get_track(track_id)
    if track is None:
        return None, None
    clip = next(
        (c for c in track.arrangement_clips if abs(c.start_time - start_time) < 0.001),
        None,
    )
    return track, clip


def _clip_info(clip):
    info = {
        "start_time": clip.start_time,
        "end_time": clip.end_time,
        "length": clip.length,
        "name": clip.name,
        "color": clip.color,
        "color_index": clip.color_index,
        "is_midi_clip": clip.is_midi_clip,
        "is_audio_clip": clip.is_audio_clip,
        "looping": clip.looping,
        "loop_start": clip.loop_start,
        "loop_end": clip.loop_end,
        "muted": clip.muted,
        "is_playing": clip.is_playing,
    }
    return info


def _get_param(track, device_id, param_name):
    """Find a DeviceParameter by device_id + param_name on a track."""
    devices = list(track.devices)
    if device_id < 0 or device_id >= len(devices):
        return None
    for param in devices[device_id].parameters:
        if param.name == param_name:
            return param
    return None


def register(server):

    # ------------------------------------------------------------------ #
    # Arrangement clips — read                                             #
    # ------------------------------------------------------------------ #

    @server.route("GET", "/live/tracks/{track_id}/arrangement_clips")
    def list_arrangement_clips(track_id, body=None):
        track = _get_track(track_id)
        if track is None:
            return {"error": f"track {track_id} not found"}
        clips = [_clip_info(c) for c in track.arrangement_clips]
        return {"clips": clips}

    @server.route("GET", "/live/tracks/{track_id}/arrangement_clips/{start_time}")
    def get_arrangement_clip(track_id, start_time, body=None):
        track, clip = _get_arrangement_clip(track_id, float(start_time))
        if clip is None:
            return {"error": f"no arrangement clip at start_time={start_time} on track {track_id}"}
        return _clip_info(clip)

    # ------------------------------------------------------------------ #
    # Arrangement clips — create / delete                                  #
    # ------------------------------------------------------------------ #

    @server.route("POST", "/live/tracks/{track_id}/arrangement_clips/create")
    def create_arrangement_clip(track_id, body=None):
        track = _get_track(track_id)
        if track is None:
            return {"error": f"track {track_id} not found"}
        if not track.has_midi_input:
            return {"error": "only MIDI tracks support creating clips"}
        b = body or {}
        start_time = float(b.get("start_time", 0))
        length = float(b.get("length", 4.0))
        name = b.get("name", "")
        try:
            track.create_midi_clip(start_time, length)
        except Exception as e:
            return {"error": f"create_midi_clip failed: {e}"}
        # find the newly created clip
        clip = next(
            (c for c in track.arrangement_clips if abs(c.start_time - start_time) < 0.001),
            None,
        )
        if clip is None:
            return {"error": "clip created but not found — start_time may have been snapped"}
        if name:
            clip.name = name
        return {"status": "ok", **_clip_info(clip)}

    @server.route("DELETE", "/live/tracks/{track_id}/arrangement_clips/{start_time}")
    def delete_arrangement_clip(track_id, start_time, body=None):
        track, clip = _get_arrangement_clip(track_id, float(start_time))
        if clip is None:
            return {"error": f"no arrangement clip at start_time={start_time} on track {track_id}"}
        try:
            track.delete_clip(clip)
        except Exception as e:
            return {"error": f"delete_clip failed: {e}"}
        return {"status": "ok"}

    # ------------------------------------------------------------------ #
    # Arrangement clips — move / resize / loop                             #
    # ------------------------------------------------------------------ #

    @server.route("POST", "/live/tracks/{track_id}/arrangement_clips/{start_time}/move")
    def move_arrangement_clip(track_id, start_time, body=None):
        track, clip = _get_arrangement_clip(track_id, float(start_time))
        if clip is None:
            return {"error": f"no arrangement clip at start_time={start_time} on track {track_id}"}
        new_position = (body or {}).get("position")
        if new_position is None:
            return {"error": "missing 'position'"}
        clip.position = float(new_position)
        return {"status": "ok", **_clip_info(clip)}

    @server.route("POST", "/live/tracks/{track_id}/arrangement_clips/{start_time}/resize")
    def resize_arrangement_clip(track_id, start_time, body=None):
        track, clip = _get_arrangement_clip(track_id, float(start_time))
        if clip is None:
            return {"error": f"no arrangement clip at start_time={start_time} on track {track_id}"}
        b = body or {}
        if "end_time" in b:
            clip.end_time = float(b["end_time"])
        if "start_time" in b:
            clip.start_time = float(b["start_time"])
        return {"status": "ok", **_clip_info(clip)}

    @server.route("POST", "/live/tracks/{track_id}/arrangement_clips/{start_time}/loop")
    def set_arrangement_clip_loop(track_id, start_time, body=None):
        track, clip = _get_arrangement_clip(track_id, float(start_time))
        if clip is None:
            return {"error": f"no arrangement clip at start_time={start_time} on track {track_id}"}
        b = body or {}
        if "looping" in b:
            clip.looping = bool(b["looping"])
        if "loop_start" in b:
            clip.loop_start = float(b["loop_start"])
        if "loop_end" in b:
            clip.loop_end = float(b["loop_end"])
        return {"status": "ok", **_clip_info(clip)}

    @server.route("POST", "/live/tracks/{track_id}/arrangement_clips/{start_time}/name")
    def rename_arrangement_clip(track_id, start_time, body=None):
        track, clip = _get_arrangement_clip(track_id, float(start_time))
        if clip is None:
            return {"error": f"no arrangement clip at start_time={start_time} on track {track_id}"}
        name = (body or {}).get("name")
        if name is None:
            return {"error": "missing 'name'"}
        clip.name = str(name)
        return {"status": "ok", "name": clip.name}

    @server.route("POST", "/live/tracks/{track_id}/arrangement_clips/{start_time}/mute")
    def mute_arrangement_clip(track_id, start_time, body=None):
        track, clip = _get_arrangement_clip(track_id, float(start_time))
        if clip is None:
            return {"error": f"no arrangement clip at start_time={start_time} on track {track_id}"}
        muted = bool((body or {}).get("muted", not clip.muted))
        clip.muted = muted
        return {"status": "ok", "muted": clip.muted}

    # ------------------------------------------------------------------ #
    # Session → Arrangement                                                #
    # ------------------------------------------------------------------ #

    @server.route("POST", "/live/tracks/{track_id}/clips/{clip_id}/duplicate_to_arrangement")
    def duplicate_to_arrangement(track_id, clip_id, body=None):
        track = _get_track(track_id)
        if track is None:
            return {"error": f"track {track_id} not found"}
        slots = list(track.clip_slots)
        if clip_id < 0 or clip_id >= len(slots):
            return {"error": f"clip slot {clip_id} not found on track {track_id}"}
        if not slots[clip_id].has_clip:
            return {"error": f"no clip in slot {clip_id} on track {track_id}"}
        start_time = float((body or {}).get("start_time", 0))
        try:
            # Live wants the Clip object here, not the slot index.
            track.duplicate_clip_to_arrangement(slots[clip_id].clip, start_time)
        except Exception as e:
            return {"error": f"duplicate_clip_to_arrangement failed: {e}"}
        return {"status": "ok", "start_time": start_time}

    # ------------------------------------------------------------------ #
    # Clip envelopes (automation) — Session and Arrangement share one impl #
    # ------------------------------------------------------------------ #

    def _resolve_clip(track_id, clip_ref, is_arrangement):
        """Return (track, clip) for either arrangement (float start_time) or session (int slot)."""
        track = _get_track(track_id)
        if track is None:
            return None, None
        if is_arrangement:
            clip = next(
                (c for c in track.arrangement_clips if abs(c.start_time - float(clip_ref)) < 0.001),
                None,
            )
        else:
            slots = list(track.clip_slots)
            idx = int(clip_ref)
            if idx < 0 or idx >= len(slots) or not slots[idx].has_clip:
                return track, None
            clip = slots[idx].clip
        return track, clip

    def _envelope_for_param(clip, param, create=False):
        env = clip.automation_envelope(param)
        if env is None and create:
            env = clip.create_automation_envelope(param)
        return env

    def _clip_or_error(track_id, clip_ref, is_arrangement):
        track, clip = _resolve_clip(track_id, clip_ref, is_arrangement)
        if track is None:
            return None, None, {"error": f"track {track_id} not found"}
        if clip is None:
            where = "arrangement at start_time" if is_arrangement else "slot"
            return track, None, {"error": f"no clip in {where} {clip_ref} on track {track_id}"}
        return track, clip, None

    # --- shared implementations, addressed by either clip kind ---

    def _env_list(track_id, clip_ref, is_arrangement):
        track, clip, err = _clip_or_error(track_id, clip_ref, is_arrangement)
        if err:
            return err
        envelopes = []
        if clip.has_envelopes:
            for device_id, device in enumerate(track.devices):
                for param in device.parameters:
                    if clip.automation_envelope(param) is not None:
                        envelopes.append({
                            "param_name": param.name,
                            "device_name": device.name,
                            "device_id": device_id,
                        })
        return {"envelopes": envelopes}

    def _env_events(track_id, clip_ref, device_id, param_name, body, is_arrangement):
        track, clip, err = _clip_or_error(track_id, clip_ref, is_arrangement)
        if err:
            return err
        param = _get_param(track, device_id, param_name)
        if param is None:
            return {"error": f"parameter '{param_name}' not found on device {device_id}"}
        env = clip.automation_envelope(param)
        if env is None:
            return {"events": [], "has_envelope": False}
        b = body or {}
        from_time = float(b.get("from_time", 0))
        to_time = float(b.get("to_time", clip.length))
        try:
            events = [
                {"time": e.time, "value": e.value}
                for e in env.events_in_range(from_time, to_time)
            ]
        except Exception as e:
            return {"error": f"events_in_range failed: {e}"}
        return {"has_envelope": True, "events": events}

    def _env_insert(track_id, clip_ref, device_id, param_name, body, is_arrangement):
        track, clip, err = _clip_or_error(track_id, clip_ref, is_arrangement)
        if err:
            return err
        param = _get_param(track, device_id, param_name)
        if param is None:
            return {"error": f"parameter '{param_name}' not found on device {device_id}"}
        b = body or {}
        time = b.get("time")
        value = b.get("value")
        if time is None or value is None:
            return {"error": "missing 'time' or 'value'"}
        # NOTE: duration 0 inserts a zero-width step, which is inaudible. To build a
        # continuous curve each step must reach the next breakpoint.
        duration = float(b.get("duration", 0.0))
        env = _envelope_for_param(clip, param, create=True)
        if env is None:
            return {"error": "failed to create automation envelope"}
        try:
            env.insert_step(float(time), duration, float(value))
        except Exception as e:
            return {"error": f"insert_step failed: {e}"}
        return {"status": "ok"}

    def _env_delete_range(track_id, clip_ref, device_id, param_name, body, is_arrangement):
        track, clip, err = _clip_or_error(track_id, clip_ref, is_arrangement)
        if err:
            return err
        param = _get_param(track, device_id, param_name)
        if param is None:
            return {"error": f"parameter '{param_name}' not found on device {device_id}"}
        b = body or {}
        from_time = float(b.get("from_time", 0))
        to_time = float(b.get("to_time", clip.length))
        env = clip.automation_envelope(param)
        if env is None:
            return {"status": "ok", "note": "no envelope existed"}
        try:
            env.delete_events_in_range(from_time, to_time)
        except Exception as e:
            return {"error": f"delete_events_in_range failed: {e}"}
        return {"status": "ok"}

    def _env_clear(track_id, clip_ref, device_id, param_name, is_arrangement):
        track, clip, err = _clip_or_error(track_id, clip_ref, is_arrangement)
        if err:
            return err
        param = _get_param(track, device_id, param_name)
        if param is None:
            return {"error": f"parameter '{param_name}' not found on device {device_id}"}
        try:
            clip.clear_envelope(param)
        except Exception as e:
            return {"error": f"clear_envelope failed: {e}"}
        return {"status": "ok"}

    # --- Session clip envelopes (clip_id = clip slot index) ---

    @server.route("GET", "/live/tracks/{track_id}/clips/{clip_id}/envelopes")
    def list_session_envelopes(track_id, clip_id, body=None):
        return _env_list(track_id, clip_id, False)

    @server.route("GET", "/live/tracks/{track_id}/clips/{clip_id}/envelopes/{device_id}/{param_name}")
    def get_session_envelope_events(track_id, clip_id, device_id, param_name, body=None):
        return _env_events(track_id, clip_id, device_id, param_name, body, False)

    @server.route("POST", "/live/tracks/{track_id}/clips/{clip_id}/envelopes/{device_id}/{param_name}/insert")
    def insert_session_envelope_step(track_id, clip_id, device_id, param_name, body=None):
        return _env_insert(track_id, clip_id, device_id, param_name, body, False)

    @server.route("DELETE", "/live/tracks/{track_id}/clips/{clip_id}/envelopes/{device_id}/{param_name}/range")
    def delete_session_envelope_range(track_id, clip_id, device_id, param_name, body=None):
        return _env_delete_range(track_id, clip_id, device_id, param_name, body, False)

    @server.route("DELETE", "/live/tracks/{track_id}/clips/{clip_id}/envelopes/{device_id}/{param_name}")
    def clear_session_envelope(track_id, clip_id, device_id, param_name, body=None):
        return _env_clear(track_id, clip_id, device_id, param_name, False)

    # --- Arrangement clip envelopes (addressed by start_time, like every other
    #     arrangement route). Unlike Session clips, an arrangement clip's envelope
    #     spans the clip's whole length, so it can express a long-form arc. ---

    @server.route("GET", "/live/tracks/{track_id}/arrangement_clips/{start_time}/envelopes")
    def list_arrangement_envelopes(track_id, start_time, body=None):
        return _env_list(track_id, start_time, True)

    @server.route("GET", "/live/tracks/{track_id}/arrangement_clips/{start_time}/envelopes/{device_id}/{param_name}")
    def get_arrangement_envelope_events(track_id, start_time, device_id, param_name, body=None):
        return _env_events(track_id, start_time, device_id, param_name, body, True)

    @server.route("POST", "/live/tracks/{track_id}/arrangement_clips/{start_time}/envelopes/{device_id}/{param_name}/insert")
    def insert_arrangement_envelope_step(track_id, start_time, device_id, param_name, body=None):
        return _env_insert(track_id, start_time, device_id, param_name, body, True)

    @server.route("DELETE", "/live/tracks/{track_id}/arrangement_clips/{start_time}/envelopes/{device_id}/{param_name}/range")
    def delete_arrangement_envelope_range(track_id, start_time, device_id, param_name, body=None):
        return _env_delete_range(track_id, start_time, device_id, param_name, body, True)

    @server.route("DELETE", "/live/tracks/{track_id}/arrangement_clips/{start_time}/envelopes/{device_id}/{param_name}")
    def clear_arrangement_envelope(track_id, start_time, device_id, param_name, body=None):
        return _env_clear(track_id, start_time, device_id, param_name, True)
