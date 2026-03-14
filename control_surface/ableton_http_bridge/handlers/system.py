"""System endpoints: ping, info, state."""

from ableton.v3.live import util


def _param_value(param):
    return {"value": param.value, "display": param.str_for_value(param.value)}


def register(server):
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
