"""System endpoints: ping, info, state, debug."""

from ableton.v3.live import util


def _param_value(param):
    return {"value": param.value, "display": param.str_for_value(param.value)}


def register(server):
    @server.route("GET", "/live/debug/methods/{obj_type}")
    def debug_methods(obj_type, body=None):
        song = util.song()
        targets = {
            "song": song,
            "track": list(song.tracks)[0] if song.tracks else None,
            "clip": None,
            "device": None,
            "return": list(song.return_tracks)[0] if song.return_tracks else None,
            "master": song.master_track,
        }
        if obj_type == "clip":
            for track in song.tracks:
                for slot in track.clip_slots:
                    if slot.has_clip:
                        targets["clip"] = slot.clip
                        break
                if targets["clip"]:
                    break
        if obj_type == "device":
            for track in song.tracks:
                if track.devices:
                    targets["device"] = list(track.devices)[0]
                    break
        obj = targets.get(obj_type)
        if obj is None:
            return {"error": f"no {obj_type} found"}
        members = sorted([m for m in dir(obj) if not m.startswith("_")])
        return {"type": obj_type, "members": members}

    @server.route("GET", "/live/debug/device/{track_id}/{device_id}")
    def debug_device(track_id, device_id, body=None):
        song = util.song()
        tracks = list(song.tracks)
        if track_id < 0 or track_id >= len(tracks):
            return {"error": "track not found"}
        devices = list(tracks[track_id].devices)
        if device_id < 0 or device_id >= len(devices):
            return {"error": "device not found"}
        dev = devices[device_id]
        members = sorted([m for m in dir(dev) if not m.startswith("_")])
        info = {"class_name": dev.class_name, "name": dev.name}
        try:
            info["can_have_chains"] = dev.can_have_chains
        except Exception:
            pass
        try:
            info["can_have_drum_pads"] = dev.can_have_drum_pads
        except Exception:
            pass
        try:
            info["chains_count"] = len(dev.chains)
        except Exception:
            info["chains_count"] = "N/A"
        try:
            info["drum_pads_count"] = len(dev.drum_pads)
        except Exception:
            info["drum_pads_count"] = "N/A"
        info["members"] = members
        return info

    @server.route("GET", "/live/ping")
    def ping(body=None):
        return {"status": "ok"}

    @server.route("GET", "/live/info")
    def info(body=None):
        song = util.song()
        return {
            "tempo": song.tempo,
            "signature_numerator": song.signature_numerator,
            "signature_denominator": song.signature_denominator,
            "track_count": len(song.tracks),
            "scene_count": len(song.scenes),
            "is_playing": song.is_playing,
        }

    @server.route("GET", "/live/state")
    def full_state(body=None):
        song = util.song()
        transport = {
            "tempo": song.tempo,
            "signature_numerator": song.signature_numerator,
            "signature_denominator": song.signature_denominator,
            "is_playing": song.is_playing,
            "is_recording": song.record_mode,
            "current_song_time": song.current_song_time,
            "loop": song.loop,
            "loop_start": song.loop_start,
            "loop_length": song.loop_length,
            "metronome": song.metronome,
        }
        tracks = []
        playing_clips = []
        for i, track in enumerate(song.tracks):
            tracks.append({
                "id": i,
                "name": track.name,
                "type": "audio" if not track.has_midi_input else "midi",
                "arm": track.arm if hasattr(track, "arm") else False,
                "solo": track.solo,
                "mute": track.mute,
                "volume": _param_value(track.mixer_device.volume),
                "pan": _param_value(track.mixer_device.panning),
                "device_count": len(track.devices),
            })
            slot_idx = track.playing_slot_index
            if slot_idx >= 0 and track.clip_slots[slot_idx].has_clip:
                playing_clips.append({
                    "track_id": i,
                    "track_name": track.name,
                    "clip_id": slot_idx,
                    "clip_name": track.clip_slots[slot_idx].clip.name,
                })
        return {
            "transport": transport,
            "tracks": tracks,
            "playing_clips": playing_clips,
            "scene_count": len(song.scenes),
        }
