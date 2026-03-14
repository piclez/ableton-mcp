"""System endpoints: ping, info."""

from ableton.v3.live import util


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
