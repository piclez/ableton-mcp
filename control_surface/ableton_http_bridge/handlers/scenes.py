"""Scene endpoints: list, create, fire, duplicate, delete, rename, select."""

from ableton.v3.live import util


def _get_scene(scene_id):
    scenes = list(util.song().scenes)
    if scene_id < 0 or scene_id >= len(scenes):
        return None
    return scenes[scene_id]


def _scene_info(index, scene):
    return {
        "id": index,
        "name": scene.name,
        "tempo": scene.tempo if scene.tempo > 0 else None,
        "is_triggered": scene.is_triggered,
    }


def register(server):
    @server.route("GET", "/live/scenes")
    def list_scenes(body=None):
        return {
            "scenes": [
                _scene_info(i, s) for i, s in enumerate(util.song().scenes)
            ]
        }

    @server.route("POST", "/live/scenes/create")
    def create_scene(body=None):
        song = util.song()
        index = len(song.scenes)
        song.create_scene(index)
        scene = song.scenes[index]
        if body and "name" in body:
            scene.name = body["name"]
        return {"status": "ok", **_scene_info(index, scene)}

    @server.route("POST", "/live/scenes/{scene_id}/fire")
    def fire_scene(scene_id, body=None):
        scene = _get_scene(scene_id)
        if scene is None:
            return {"error": f"scene {scene_id} not found"}
        scene.fire()
        return {"status": "ok"}

    @server.route("POST", "/live/scenes/{scene_id}/name")
    def set_name(scene_id, body=None):
        scene = _get_scene(scene_id)
        if scene is None:
            return {"error": f"scene {scene_id} not found"}
        name = body.get("name") if body else None
        if name is None:
            return {"error": "missing 'name'"}
        scene.name = str(name)
        return {"status": "ok", "name": scene.name}

    @server.route("POST", "/live/scenes/{scene_id}/duplicate")
    def duplicate_scene(scene_id, body=None):
        scene = _get_scene(scene_id)
        if scene is None:
            return {"error": f"scene {scene_id} not found"}
        util.song().duplicate_scene(scene_id)
        return {"status": "ok"}

    @server.route("POST", "/live/scenes/{scene_id}/select")
    def select_scene(scene_id, body=None):
        scene = _get_scene(scene_id)
        if scene is None:
            return {"error": f"scene {scene_id} not found"}
        util.song().view.selected_scene = scene
        return {"status": "ok"}

    @server.route("DELETE", "/live/scenes/{scene_id}")
    def delete_scene(scene_id, body=None):
        scene = _get_scene(scene_id)
        if scene is None:
            return {"error": f"scene {scene_id} not found"}
        song = util.song()
        if len(song.scenes) <= 1:
            return {"error": "cannot delete last scene"}
        song.delete_scene(scene_id)
        return {"status": "ok"}
