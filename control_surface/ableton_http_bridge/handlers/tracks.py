"""Track endpoints: list, volume, pan, arm, solo, mute, send, name, duplicate, stop, select."""

from ableton.v3.live import util


def _param_value(param):
    """Return raw value + display string for a DeviceParameter."""
    return {"value": param.value, "display": param.str_for_value(param.value)}


def _track_info(index, track):
    return {
        "id": index,
        "name": track.name,
        "type": "return" if track in util.song().return_tracks else (
            "master" if track == util.song().master_track else "audio" if not track.has_midi_input else "midi"
        ),
        "arm": track.arm if hasattr(track, "arm") else False,
        "solo": track.solo,
        "mute": track.mute,
        "volume": _param_value(track.mixer_device.volume),
        "pan": _param_value(track.mixer_device.panning),
    }


def _get_all_tracks():
    song = util.song()
    tracks = []
    for i, track in enumerate(song.tracks):
        tracks.append(_track_info(i, track))
    return tracks


def _get_track(track_id):
    song = util.song()
    tracks = list(song.tracks)
    if track_id < 0 or track_id >= len(tracks):
        return None
    return tracks[track_id]


def register(server):
    @server.route("GET", "/live/tracks")
    def list_tracks(body=None):
        return {"tracks": _get_all_tracks()}

    @server.route("GET", "/live/tracks/{track_id}")
    def get_track(track_id, body=None):
        track = _get_track(track_id)
        if track is None:
            return {"error": f"track {track_id} not found"}
        info = _track_info(track_id, track)
        info["sends"] = [
            {"index": i, **_param_value(s)}
            for i, s in enumerate(track.mixer_device.sends)
        ]
        return info

    @server.route("POST", "/live/tracks/{track_id}/arm")
    def set_arm(track_id, body=None):
        track = _get_track(track_id)
        if track is None:
            return {"error": f"track {track_id} not found"}
        armed = body.get("armed", not track.arm) if body else not track.arm
        track.arm = bool(armed)
        return {"status": "ok", "arm": track.arm}

    @server.route("POST", "/live/tracks/{track_id}/solo")
    def set_solo(track_id, body=None):
        track = _get_track(track_id)
        if track is None:
            return {"error": f"track {track_id} not found"}
        solo = body.get("solo", not track.solo) if body else not track.solo
        track.solo = bool(solo)
        return {"status": "ok", "solo": track.solo}

    @server.route("POST", "/live/tracks/{track_id}/mute")
    def set_mute(track_id, body=None):
        track = _get_track(track_id)
        if track is None:
            return {"error": f"track {track_id} not found"}
        mute = body.get("mute", not track.mute) if body else not track.mute
        track.mute = bool(mute)
        return {"status": "ok", "mute": track.mute}

    @server.route("POST", "/live/tracks/{track_id}/volume")
    def set_volume(track_id, body=None):
        track = _get_track(track_id)
        if track is None:
            return {"error": f"track {track_id} not found"}
        value = body.get("value") if body else None
        if value is None:
            return {"error": "missing 'value'"}
        track.mixer_device.volume.value = float(value)
        return {"status": "ok", "volume": _param_value(track.mixer_device.volume)}

    @server.route("POST", "/live/tracks/{track_id}/pan")
    def set_pan(track_id, body=None):
        track = _get_track(track_id)
        if track is None:
            return {"error": f"track {track_id} not found"}
        value = body.get("value") if body else None
        if value is None:
            return {"error": "missing 'value'"}
        track.mixer_device.panning.value = float(value)
        return {"status": "ok", "pan": _param_value(track.mixer_device.panning)}

    @server.route("POST", "/live/tracks/{track_id}/send")
    def set_send(track_id, body=None):
        track = _get_track(track_id)
        if track is None:
            return {"error": f"track {track_id} not found"}
        send_index = body.get("send_index") if body else None
        value = body.get("value") if body else None
        if send_index is None or value is None:
            return {"error": "missing 'send_index' or 'value'"}
        sends = track.mixer_device.sends
        if send_index < 0 or send_index >= len(sends):
            return {"error": f"send {send_index} not found"}
        sends[send_index].value = float(value)
        return {"status": "ok", "send_index": send_index, **_param_value(sends[send_index])}

    @server.route("POST", "/live/tracks/{track_id}/name")
    def set_name(track_id, body=None):
        track = _get_track(track_id)
        if track is None:
            return {"error": f"track {track_id} not found"}
        name = body.get("name") if body else None
        if name is None:
            return {"error": "missing 'name'"}
        track.name = str(name)
        return {"status": "ok", "name": track.name}

    @server.route("POST", "/live/tracks/{track_id}/select")
    def select_track(track_id, body=None):
        track = _get_track(track_id)
        if track is None:
            return {"error": f"track {track_id} not found"}
        util.song().view.selected_track = track
        return {"status": "ok"}

    @server.route("POST", "/live/tracks/{track_id}/duplicate")
    def duplicate_track(track_id, body=None):
        track = _get_track(track_id)
        if track is None:
            return {"error": f"track {track_id} not found"}
        util.song().duplicate_track(track_id)
        return {"status": "ok"}

    @server.route("POST", "/live/tracks/{track_id}/stop")
    def stop_track(track_id, body=None):
        track = _get_track(track_id)
        if track is None:
            return {"error": f"track {track_id} not found"}
        track.stop_all_clips()
        return {"status": "ok"}

    @server.route("GET", "/live/playing")
    def get_playing(body=None):
        clips = []
        for i, track in enumerate(util.song().tracks):
            slot = track.playing_slot_index
            if slot >= 0:
                clip_slot = track.clip_slots[slot]
                if clip_slot.has_clip:
                    clips.append({
                        "track_id": i,
                        "track_name": track.name,
                        "clip_id": slot,
                        "clip_name": clip_slot.clip.name,
                    })
        return {"playing_clips": clips}

    @server.route("GET", "/live/armed")
    def get_armed(body=None):
        armed = []
        for i, track in enumerate(util.song().tracks):
            if hasattr(track, "arm") and track.arm:
                armed.append({"id": i, "name": track.name})
        return {"armed_tracks": armed}
