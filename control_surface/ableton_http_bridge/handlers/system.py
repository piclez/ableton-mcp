"""System endpoints: ping, info, state, debug."""

import re

from ableton.v3.live import util


def _param_value(param):
    return {"value": param.value, "display": param.str_for_value(param.value)}


_ROLE_KEYWORDS = [
    # kick
    (["kick", "bd", "bass drum", "bassdrum", "kik", "kck",
      "4 on floor", "4onfloor", "909", "808 kick", "606"], "drums", "kick"),
    # snare / clap
    (["snare", "snr", "clap", "clp", "rimshot", "rim",
      "backbeat", "snap", "popcorn"], "drums", "snare"),
    # hihat / cymbal
    (["hihat", "hi-hat", "hi hat", "hh", "hat", "cymbal",
      "ride", "crash", "open hat", "closed hat", "oh", "ch",
      "zap", "tick"], "drums", "hihat"),
    # perc
    (["tom", "perc", "percussion", "conga", "bongo", "clave",
      "shaker", "tamb", "cowbell", "woodblock", "maracas",
      "tambourine", "tribal", "afro", "latin"], "drums", "perc"),
    # bass (before generic drums — "beat that bass" should be bass, not drums)
    (["bass", "sub", "808", "reese", "wobble", "growl",
      "acid", "tb-303", "tb303", "303", "subbass", "low end",
      "lowend", "deep", "pump"], "bass", None),
    # generic drums
    (["drum", "drm", "beat", "kit", "groove", "loop"], "drums", None),
    # lead
    (["lead", "melody", "mel", "arp", "arpegg", "stab",
      "hook", "riff", "motif", "pluck", "saw lead",
      "synth lead", "mono"], "lead", None),
    # chord / pad
    (["chord", "pad", "harmony", "atmo", "atmosphere",
      "string", "keys", "piano", "ep", "organ", "rhodes",
      "wurli", "stab chord", "spread", "lush", "ambient",
      "texture", "drone", "wash"], "chord", None),
    # vocal
    (["vocal", "vox", "voice", "sing", "chant",
      "spoken", "rap", "sample vox", "hook vox"], "vocal", None),
    # sidechain trigger
    (["sc", "sidechain", "side chain", "side-chain",
      "trigger", "trig", "sc trigger"], "fx", "sidechain"),
    # fx
    (["fx", "sfx", "foley", "riser", "sweep", "down",
      "uplifter", "downlifter", "impact", "hit", "noise",
      "white", "pink", "transition", "fill", "break"], "fx", None),
    # guitar
    (["guitar", "gtr", "guit"], "guitar", None),
    # brass
    (["brass", "horn", "sax", "trumpet", "trombone"], "brass", None),
]


# MIDI note ranges for drum subrole inference from pad notes
# note 36=C1 kick area, 38=D1 snare area, 42/44/46 hihat area, 41-50 perc/tom area
_KICK_NOTES  = {35, 36}
_SNARE_NOTES = {38, 39, 40}
_HIHAT_NOTES = {42, 44, 46}
_PERC_NOTES  = set(range(37, 82)) - _KICK_NOTES - _SNARE_NOTES - _HIHAT_NOTES


def _drum_rack_subrole(track):
    """Infer subrole from occupied pad names and notes."""
    try:
        drum_dev = next(
            (d for d in track.devices if d.class_name == "DrumGroupDevice"), None
        )
        if drum_dev is None:
            return None
        # collect roles of occupied pads (chain_count > 0) via name heuristic + note fallback
        pad_roles = set()
        for pad in drum_dev.visible_drum_pads:
            if len(list(pad.chains)) > 0:
                # try name first
                pad_role, pad_subrole = _infer_role(pad.name)
                if pad_role == "drums" and pad_subrole is not None:
                    pad_roles.add(pad_subrole)
                elif pad_role == "unknown":
                    # fallback to note number
                    note = pad.note
                    if note in _KICK_NOTES:
                        pad_roles.add("kick")
                    elif note in _SNARE_NOTES:
                        pad_roles.add("snare")
                    elif note in _HIHAT_NOTES:
                        pad_roles.add("hihat")
                    else:
                        pad_roles.add("perc")
        pad_roles.discard(None)
        if not pad_roles:
            return None
        # single subrole → return it
        if len(pad_roles) == 1:
            return pad_roles.pop()
        # kick only + perc → kick
        if pad_roles == {"kick", "perc"} or pad_roles == {"kick"}:
            return "kick"
        return None
    except Exception as e:
        return "err:" + str(e)


def _infer_role(name):
    name_lower = name.lower()
    for keywords, role, subrole in _ROLE_KEYWORDS:
        for kw in keywords:
            # multi-word keywords: substring match; single-word: word boundary
            if " " in kw or "-" in kw:
                if kw in name_lower:
                    return role, subrole
            else:
                if re.search(r"\b" + re.escape(kw) + r"\b", name_lower):
                    return role, subrole
    return "unknown", None


def _compute_energy(bpm, roles):
    has_drums = "drums" in roles
    has_bass = "bass" in roles
    if bpm >= 145 or (bpm >= 130 and has_drums and has_bass):
        return "high"
    if bpm >= 110 or (has_drums and has_bass):
        return "medium"
    return "low"


def _compute_density(roles):
    unique = len(set(r for r in roles if r != "unknown"))
    if unique >= 4:
        return "high"
    if unique >= 2:
        return "medium"
    return "low"


_GENRE_RULES = [
    # (bpm_min, bpm_max, required_roles, genre)
    (160, 200, {"drums"},           "dnb"),
    (145, 165, {"drums"},           "techno"),
    (128, 145, {"drums", "bass"},   "techno"),
    (120, 132, {"drums", "chord"},  "house"),
    (120, 132, {"drums"},           "house"),
    (138, 150, {"drums", "chord"},  "trance"),
    ( 60, 100, {"bass"},            "hiphop"),
    ( 60, 100, {"drums", "bass"},   "hiphop"),
    (100, 120, {"drums", "bass"},   "trap"),
]


def _guess_genre(bpm, roles):
    role_set = set(roles)
    for bmin, bmax, required, genre in _GENRE_RULES:
        if bmin <= bpm < bmax and required.issubset(role_set):
            return genre
    return "unknown"


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

    @server.route("GET", "/live/session/structure")
    def session_structure(body=None):
        song = util.song()
        tracks = []
        for i, track in enumerate(song.tracks):
            role, subrole = _infer_role(track.name)
            if subrole is None and role == "drums":
                subrole = _drum_rack_subrole(track)
            elif role == "unknown":
                for d in track.devices:
                    if d.class_name == "DrumGroupDevice":
                        role, subrole = "drums", _drum_rack_subrole(track)
                        break
            tracks.append({
                "id": i,
                "name": track.name,
                "type": "audio" if not track.has_midi_input else "midi",
                "devices": [d.class_name for d in track.devices],
                "clip_count": sum(1 for s in track.clip_slots if s.has_clip),
                "active_clips": [
                    {"id": j, "name": s.clip.name}
                    for j, s in enumerate(track.clip_slots)
                    if s.has_clip and s.clip.is_playing
                ],
                "mute": track.mute,
                "solo": track.solo,
                "role": role,
                "subrole": subrole,
            })
        roles = [t["role"] for t in tracks]
        return {
            "bpm": song.tempo,
            "genre_guess": _guess_genre(song.tempo, roles),
            "energy_level": _compute_energy(song.tempo, roles),
            "density": _compute_density(roles),
            "tracks": tracks,
        }

    @server.route("GET", "/live/browser/info")
    def browser_info(body=None):
        import Live
        app = Live.Application.get_application()
        browser = app.browser
        members = sorted([m for m in dir(browser) if not m.startswith("_")])
        categories = {}
        for cat in ["instruments", "audio_effects", "midi_effects", "drums",
                    "samples", "clips", "packs", "user_library", "plugins",
                    "max_for_live"]:
            try:
                item = getattr(browser, cat)
                categories[cat] = {
                    "name": item.name,
                    "is_folder": item.is_folder,
                    "children_count": len(list(item.children)),
                }
            except Exception as e:
                categories[cat] = {"error": str(e)}
        has_load_item = hasattr(browser, "load_item")
        return {"members": members, "categories": categories, "has_load_item": has_load_item}

    @server.route("GET", "/live/browser/tree/{category}")
    def browser_tree(category, body=None):
        import Live
        app = Live.Application.get_application()
        browser = app.browser
        try:
            root = getattr(browser, category)
        except AttributeError:
            return {"error": f"unknown category '{category}'"}
        def _collect(item, depth, max_depth=3):
            result = {"name": item.name, "is_folder": False, "is_loadable": False}
            try:
                result["is_folder"] = item.is_folder
                result["is_loadable"] = item.is_loadable
            except Exception:
                pass
            if depth < max_depth:
                try:
                    if item.is_folder:
                        result["children"] = [_collect(c, depth + 1, max_depth) for c in item.children]
                except Exception:
                    pass
            return result
        try:
            children = [_collect(c, 0) for c in root.children]
            return {"category": category, "name": root.name, "children": children}
        except Exception as e:
            return {"error": str(e)}
