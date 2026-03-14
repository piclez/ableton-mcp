"""Transport endpoints: play, stop, record, BPM, loop, position, undo, redo."""

from ableton.v3.live import util


def register(server):
    @server.route("GET", "/live/transport")
    def get_transport(body=None):
        song = util.song()
        return {
            "tempo": song.tempo,
            "signature_numerator": song.signature_numerator,
            "signature_denominator": song.signature_denominator,
            "is_playing": song.is_playing,
            "is_recording": song.record_mode,
            "current_song_time": song.current_song_time,
            "song_length": song.song_length,
            "loop_start": song.loop_start,
            "loop_length": song.loop_length,
            "loop": song.loop,
            "metronome": song.metronome,
        }

    @server.route("POST", "/live/transport/play")
    def play(body=None):
        song = util.song()
        song.start_playing()
        return {"status": "ok"}

    @server.route("POST", "/live/transport/stop")
    def stop(body=None):
        song = util.song()
        song.stop_playing()
        return {"status": "ok"}

    @server.route("POST", "/live/transport/record")
    def record(body=None):
        song = util.song()
        song.record_mode = not song.record_mode
        return {"status": "ok", "record_mode": song.record_mode}

    @server.route("POST", "/live/transport/bpm")
    def set_bpm(body=None):
        bpm = body.get("bpm") if body else None
        if bpm is None:
            return {"error": "missing 'bpm'"}
        song = util.song()
        song.tempo = float(bpm)
        return {"status": "ok", "tempo": song.tempo}

    @server.route("POST", "/live/transport/loop")
    def set_loop(body=None):
        song = util.song()
        if body:
            if "enabled" in body:
                song.loop = bool(body["enabled"])
            if "start" in body:
                song.loop_start = float(body["start"])
            if "length" in body:
                song.loop_length = float(body["length"])
        return {
            "status": "ok",
            "loop": song.loop,
            "loop_start": song.loop_start,
            "loop_length": song.loop_length,
        }

    @server.route("POST", "/live/transport/metronome")
    def set_metronome(body=None):
        song = util.song()
        if body and "enabled" in body:
            song.metronome = bool(body["enabled"])
        else:
            song.metronome = not song.metronome
        return {"status": "ok", "metronome": song.metronome}

    @server.route("POST", "/live/transport/position")
    def set_position(body=None):
        position = body.get("position") if body else None
        if position is None:
            return {"error": "missing 'position'"}
        song = util.song()
        song.current_song_time = float(position)
        return {"status": "ok", "current_song_time": song.current_song_time}

    @server.route("POST", "/live/undo")
    def undo(body=None):
        song = util.song()
        song.undo()
        return {"status": "ok"}

    @server.route("POST", "/live/redo")
    def redo(body=None):
        song = util.song()
        song.redo()
        return {"status": "ok"}
