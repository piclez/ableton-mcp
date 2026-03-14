"""Clip and note endpoints: list, create, fire, stop, duplicate, notes CRUD, loop."""

from ableton.v3.live import util


def _get_track(track_id):
    tracks = list(util.song().tracks)
    if track_id < 0 or track_id >= len(tracks):
        return None
    return tracks[track_id]


def _get_clip(track_id, clip_id):
    track = _get_track(track_id)
    if track is None:
        return None, None, None
    slots = list(track.clip_slots)
    if clip_id < 0 or clip_id >= len(slots):
        return track, None, None
    slot = slots[clip_id]
    if not slot.has_clip:
        return track, slot, None
    return track, slot, slot.clip


def _clip_info(clip_id, clip_slot):
    if not clip_slot.has_clip:
        return {"id": clip_id, "has_clip": False}
    clip = clip_slot.clip
    return {
        "id": clip_id,
        "has_clip": True,
        "name": clip.name,
        "color": clip.color,
        "color_index": clip.color_index,
        "length": clip.length,
        "is_playing": clip.is_playing,
        "is_recording": clip.is_recording,
        "looping": clip.looping,
        "loop_start": clip.loop_start,
        "loop_end": clip.loop_end,
    }


def register(server):
    @server.route("GET", "/live/tracks/{track_id}/clips")
    def list_clips(track_id, body=None):
        track = _get_track(track_id)
        if track is None:
            return {"error": f"track {track_id} not found"}
        clips = []
        for i, slot in enumerate(track.clip_slots):
            if slot.has_clip:
                clips.append(_clip_info(i, slot))
        return {"clips": clips}

    @server.route("GET", "/live/tracks/{track_id}/clips/{clip_id}")
    def get_clip(track_id, clip_id, body=None):
        _, slot, clip = _get_clip(track_id, clip_id)
        if slot is None:
            return {"error": f"clip slot {clip_id} not found on track {track_id}"}
        return _clip_info(clip_id, slot)

    @server.route("POST", "/live/tracks/{track_id}/clips/{clip_id}/fire")
    def fire_clip(track_id, clip_id, body=None):
        _, slot, _ = _get_clip(track_id, clip_id)
        if slot is None:
            return {"error": f"clip slot {clip_id} not found on track {track_id}"}
        slot.fire()
        return {"status": "ok"}

    @server.route("POST", "/live/tracks/{track_id}/clips/{clip_id}/stop")
    def stop_clip(track_id, clip_id, body=None):
        _, slot, _ = _get_clip(track_id, clip_id)
        if slot is None:
            return {"error": f"clip slot {clip_id} not found on track {track_id}"}
        slot.stop()
        return {"status": "ok"}

    @server.route("POST", "/live/tracks/{track_id}/clips/create")
    def create_clip(track_id, body=None):
        track = _get_track(track_id)
        if track is None:
            return {"error": f"track {track_id} not found"}
        length = float(body.get("length", 4.0)) if body else 4.0
        name = body.get("name", "") if body else ""
        # Find first empty slot
        for i, slot in enumerate(track.clip_slots):
            if not slot.has_clip:
                slot.create_clip(length)
                if name:
                    slot.clip.name = name
                return {"status": "ok", **_clip_info(i, slot)}
        return {"error": "no empty clip slot"}

    @server.route("POST", "/live/tracks/{track_id}/clips/{clip_id}/name")
    def set_name(track_id, clip_id, body=None):
        _, _, clip = _get_clip(track_id, clip_id)
        if clip is None:
            return {"error": f"clip {clip_id} not found on track {track_id}"}
        name = body.get("name") if body else None
        if name is None:
            return {"error": "missing 'name'"}
        clip.name = str(name)
        return {"status": "ok", "name": clip.name}

    @server.route("POST", "/live/tracks/{track_id}/clips/{clip_id}/color")
    def set_color(track_id, clip_id, body=None):
        _, _, clip = _get_clip(track_id, clip_id)
        if clip is None:
            return {"error": f"clip {clip_id} not found on track {track_id}"}
        if body and "color_index" in body:
            clip.color_index = int(body["color_index"])
        elif body and "color" in body:
            clip.color = int(body["color"])
        else:
            return {"error": "missing 'color_index' or 'color'"}
        return {"status": "ok", "color": clip.color, "color_index": clip.color_index}

    @server.route("POST", "/live/tracks/{track_id}/clips/{clip_id}/duplicate")
    def duplicate_clip(track_id, clip_id, body=None):
        track = _get_track(track_id)
        if track is None:
            return {"error": f"track {track_id} not found"}
        _, _, clip = _get_clip(track_id, clip_id)
        if clip is None:
            return {"error": f"clip {clip_id} not found on track {track_id}"}
        track.duplicate_clip_slot(clip_id)
        return {"status": "ok"}

    @server.route("POST", "/live/tracks/{track_id}/clips/{clip_id}/duplicate_loop")
    def duplicate_loop(track_id, clip_id, body=None):
        _, _, clip = _get_clip(track_id, clip_id)
        if clip is None:
            return {"error": f"clip {clip_id} not found on track {track_id}"}
        clip.duplicate_loop()
        return {"status": "ok", "loop_end": clip.loop_end, "length": clip.length}

    # --- Notes ---

    @server.route("GET", "/live/tracks/{track_id}/clips/{clip_id}/notes")
    def get_notes(track_id, clip_id, body=None):
        _, _, clip = _get_clip(track_id, clip_id)
        if clip is None:
            return {"error": f"clip {clip_id} not found on track {track_id}"}
        notes = clip.get_notes_extended(from_pitch=0, pitch_span=128,
                                        from_time=0, time_span=clip.length)
        return {
            "notes": [
                {
                    "pitch": n.pitch,
                    "time": n.start_time,
                    "duration": n.duration,
                    "velocity": n.velocity,
                    "mute": n.mute,
                }
                for n in notes
            ]
        }

    @server.route("POST", "/live/tracks/{track_id}/clips/{clip_id}/notes")
    def add_notes(track_id, clip_id, body=None):
        _, _, clip = _get_clip(track_id, clip_id)
        if clip is None:
            return {"error": f"clip {clip_id} not found on track {track_id}"}
        if not body or not isinstance(body, list):
            return {"error": "body must be a list of notes"}
        from Live.Clip import MidiNoteSpecification
        specs = []
        for n in body:
            specs.append(MidiNoteSpecification(
                pitch=int(n["pitch"]),
                start_time=float(n["time"]),
                duration=float(n.get("duration", 0.25)),
                velocity=float(n.get("velocity", 100)),
                mute=bool(n.get("mute", False)),
            ))
        clip.add_new_notes(tuple(specs))
        return {"status": "ok", "added": len(specs)}

    @server.route("DELETE", "/live/tracks/{track_id}/clips/{clip_id}/notes")
    def clear_notes(track_id, clip_id, body=None):
        _, _, clip = _get_clip(track_id, clip_id)
        if clip is None:
            return {"error": f"clip {clip_id} not found on track {track_id}"}
        clip.remove_notes_extended(from_pitch=0, pitch_span=128,
                                   from_time=0, time_span=clip.length)
        return {"status": "ok"}

    @server.route("DELETE", "/live/tracks/{track_id}/clips/{clip_id}/notes/by_pitch")
    def delete_by_pitch(track_id, clip_id, body=None):
        _, _, clip = _get_clip(track_id, clip_id)
        if clip is None:
            return {"error": f"clip {clip_id} not found on track {track_id}"}
        pitches = body.get("pitches", []) if body else []
        for pitch in pitches:
            clip.remove_notes_extended(from_pitch=int(pitch), pitch_span=1,
                                       from_time=0, time_span=clip.length)
        return {"status": "ok", "removed_pitches": pitches}

    @server.route("DELETE", "/live/tracks/{track_id}/clips/{clip_id}/notes/in_range")
    def delete_in_range(track_id, clip_id, body=None):
        _, _, clip = _get_clip(track_id, clip_id)
        if clip is None:
            return {"error": f"clip {clip_id} not found on track {track_id}"}
        start = float(body.get("start", 0)) if body else 0
        end = float(body.get("end", clip.length)) if body else clip.length
        clip.remove_notes_extended(from_pitch=0, pitch_span=128,
                                   from_time=start, time_span=end - start)
        return {"status": "ok"}

    # --- Clip Loop ---

    @server.route("POST", "/live/tracks/{track_id}/clips/{clip_id}/loop")
    def set_loop(track_id, clip_id, body=None):
        _, _, clip = _get_clip(track_id, clip_id)
        if clip is None:
            return {"error": f"clip {clip_id} not found on track {track_id}"}
        if body:
            if "enabled" in body:
                clip.looping = bool(body["enabled"])
            if "start" in body:
                clip.loop_start = float(body["start"])
            if "end" in body:
                clip.loop_end = float(body["end"])
        return {
            "status": "ok",
            "looping": clip.looping,
            "loop_start": clip.loop_start,
            "loop_end": clip.loop_end,
        }

    @server.route("POST", "/live/tracks/{track_id}/clips/{clip_id}/loop/extend")
    def extend_loop(track_id, clip_id, body=None):
        _, _, clip = _get_clip(track_id, clip_id)
        if clip is None:
            return {"error": f"clip {clip_id} not found on track {track_id}"}
        bars = int(body.get("bars", 1)) if body else 1
        song = util.song()
        bar_length = song.signature_numerator * (4.0 / song.signature_denominator)
        clip.loop_end = clip.loop_end + (bars * bar_length)
        return {
            "status": "ok",
            "loop_end": clip.loop_end,
            "length": clip.length,
        }
