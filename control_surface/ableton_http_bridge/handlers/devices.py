"""Device endpoints: list devices, parameters, set parameter, batch, enable/disable, chains."""

from ableton.v3.live import util


def _get_track(track_id):
    tracks = list(util.song().tracks)
    if track_id < 0 or track_id >= len(tracks):
        return None
    return tracks[track_id]


def _get_any_track(track_type, track_id):
    """Get a track by type: 'track', 'return', or 'master'."""
    song = util.song()
    if track_type == "return":
        returns = list(song.return_tracks)
        if track_id < 0 or track_id >= len(returns):
            return None
        return returns[track_id]
    elif track_type == "master":
        return song.master_track
    else:
        return _get_track(track_id)


def _get_device(track_id, device_id):
    track = _get_track(track_id)
    if track is None:
        return None, None
    devices = list(track.devices)
    if device_id < 0 or device_id >= len(devices):
        return track, None
    return track, devices[device_id]


def _device_info(index, device):
    return {
        "id": index,
        "name": device.name,
        "class_name": device.class_name,
        "type": str(device.type),
        "enabled": bool(device.parameters[0].value) if device.parameters else True,
    }


def _param_info(param):
    return {
        "name": param.name,
        "value": param.value,
        "display": param.str_for_value(param.value),
        "min": param.min,
        "max": param.max,
    }


def register(server):
    @server.route("GET", "/live/tracks/{track_id}/devices")
    def list_devices(track_id, body=None):
        track = _get_track(track_id)
        if track is None:
            return {"error": f"track {track_id} not found"}
        return {
            "devices": [_device_info(i, d) for i, d in enumerate(track.devices)]
        }

    @server.route("GET", "/live/tracks/{track_id}/devices/{device_id}")
    def get_device(track_id, device_id, body=None):
        _, device = _get_device(track_id, device_id)
        if device is None:
            return {"error": f"device {device_id} not found on track {track_id}"}
        info = _device_info(device_id, device)
        return info

    @server.route("GET", "/live/tracks/{track_id}/devices/{device_id}/parameters")
    def list_parameters(track_id, device_id, body=None):
        _, device = _get_device(track_id, device_id)
        if device is None:
            return {"error": f"device {device_id} not found on track {track_id}"}
        return {
            "device": device.name,
            "class_name": device.class_name,
            "parameters": [_param_info(p) for p in device.parameters],
        }

    @server.route("POST", "/live/tracks/{track_id}/devices/{device_id}/parameters/batch")
    def set_parameters_batch(track_id, device_id, body=None):
        _, device = _get_device(track_id, device_id)
        if device is None:
            return {"error": f"device {device_id} not found on track {track_id}"}
        if not body or not isinstance(body, list):
            return {"error": "body must be a list of {name, value}"}
        params_by_name = {p.name: p for p in device.parameters}
        results = []
        for item in body:
            name = item.get("name")
            value = item.get("value")
            if name in params_by_name and value is not None:
                params_by_name[name].value = float(value)
                results.append({"status": "ok", **_param_info(params_by_name[name])})
            else:
                results.append({"status": "error", "name": name, "error": "not found or missing value"})
        return {"results": results}

    @server.route("POST", "/live/tracks/{track_id}/devices/{device_id}/parameters/{name}")
    def set_parameter(track_id, device_id, name, body=None):
        _, device = _get_device(track_id, device_id)
        if device is None:
            return {"error": f"device {device_id} not found on track {track_id}"}
        value = body.get("value") if body else None
        if value is None:
            return {"error": "missing 'value'"}
        for param in device.parameters:
            if param.name == name:
                param.value = float(value)
                return {"status": "ok", **_param_info(param)}
        return {"error": f"parameter '{name}' not found"}

    @server.route("POST", "/live/tracks/{track_id}/devices/{device_id}/enabled")
    def set_enabled(track_id, device_id, body=None):
        _, device = _get_device(track_id, device_id)
        if device is None:
            return {"error": f"device {device_id} not found on track {track_id}"}
        enabled = body.get("enabled") if body else None
        if enabled is None:
            return {"error": "missing 'enabled'"}
        # Device On/Off is always the first parameter
        if device.parameters:
            device.parameters[0].value = 1.0 if enabled else 0.0
        return {"status": "ok", "enabled": bool(device.parameters[0].value)}

    # --- Chains (racks) ---

    @server.route("GET", "/live/tracks/{track_id}/devices/{device_id}/chains")
    def list_chains(track_id, device_id, body=None):
        _, device = _get_device(track_id, device_id)
        if device is None:
            return {"error": f"device {device_id} not found on track {track_id}"}
        if not device.can_have_chains:
            return {"error": f"device '{device.name}' does not support chains"}
        chains = []
        for i, chain in enumerate(device.chains):
            chains.append({
                "id": i,
                "name": chain.name,
                "device_count": len(chain.devices),
                "devices": [_device_info(j, d) for j, d in enumerate(chain.devices)],
            })
        return {"chains": chains}

    @server.route("GET", "/live/tracks/{track_id}/devices/{device_id}/chains/{chain_id}/devices/{chain_device_id}/parameters")
    def list_chain_device_params(track_id, device_id, chain_id, chain_device_id, body=None):
        _, device = _get_device(track_id, device_id)
        if device is None:
            return {"error": f"device {device_id} not found on track {track_id}"}
        if not device.can_have_chains:
            return {"error": f"device '{device.name}' does not support chains"}
        chains = list(device.chains)
        if chain_id < 0 or chain_id >= len(chains):
            return {"error": f"chain {chain_id} not found"}
        devices = list(chains[chain_id].devices)
        if chain_device_id < 0 or chain_device_id >= len(devices):
            return {"error": f"device {chain_device_id} not found in chain {chain_id}"}
        dev = devices[chain_device_id]
        return {
            "device": dev.name,
            "class_name": dev.class_name,
            "parameters": [_param_info(p) for p in dev.parameters],
        }

    @server.route("POST", "/live/tracks/{track_id}/devices/{device_id}/chains/{chain_id}/devices/{chain_device_id}/parameters/batch")
    def set_chain_device_params_batch(track_id, device_id, chain_id, chain_device_id, body=None):
        _, device = _get_device(track_id, device_id)
        if device is None:
            return {"error": f"device {device_id} not found on track {track_id}"}
        if not device.can_have_chains:
            return {"error": f"device '{device.name}' does not support chains"}
        chains = list(device.chains)
        if chain_id < 0 or chain_id >= len(chains):
            return {"error": f"chain {chain_id} not found"}
        devices = list(chains[chain_id].devices)
        if chain_device_id < 0 or chain_device_id >= len(devices):
            return {"error": f"device {chain_device_id} not found in chain {chain_id}"}
        dev = devices[chain_device_id]
        if not body or not isinstance(body, list):
            return {"error": "body must be a list of {name, value}"}
        params_by_name = {p.name: p for p in dev.parameters}
        results = []
        for item in body:
            name = item.get("name")
            value = item.get("value")
            if name in params_by_name and value is not None:
                params_by_name[name].value = float(value)
                results.append({"status": "ok", **_param_info(params_by_name[name])})
            else:
                results.append({"status": "error", "name": name, "error": "not found or missing value"})
        return {"results": results}

    @server.route("POST", "/live/tracks/{track_id}/devices/{device_id}/chains/{chain_id}/devices/{chain_device_id}/parameters/{name}")
    def set_chain_device_param(track_id, device_id, chain_id, chain_device_id, name, body=None):
        _, device = _get_device(track_id, device_id)
        if device is None:
            return {"error": f"device {device_id} not found on track {track_id}"}
        if not device.can_have_chains:
            return {"error": f"device '{device.name}' does not support chains"}
        chains = list(device.chains)
        if chain_id < 0 or chain_id >= len(chains):
            return {"error": f"chain {chain_id} not found"}
        devices = list(chains[chain_id].devices)
        if chain_device_id < 0 or chain_device_id >= len(devices):
            return {"error": f"device {chain_device_id} not found in chain {chain_id}"}
        dev = devices[chain_device_id]
        value = body.get("value") if body else None
        if value is None:
            return {"error": "missing 'value'"}
        for param in dev.parameters:
            if param.name == name:
                param.value = float(value)
                return {"status": "ok", **_param_info(param)}
        return {"error": f"parameter '{name}' not found"}

    # --- Drum pads ---

    @server.route("GET", "/live/tracks/{track_id}/devices/{device_id}/drum_pads")
    def list_drum_pads(track_id, device_id, body=None):
        _, device = _get_device(track_id, device_id)
        if device is None:
            return {"error": f"device {device_id} not found on track {track_id}"}
        if not device.can_have_drum_pads:
            return {"error": f"device '{device.name}' does not have drum pads"}
        pads = []
        for pad in device.visible_drum_pads:
            chains = list(pad.chains) if pad.chains else []
            pads.append({
                "note": pad.note,
                "name": pad.name,
                "mute": pad.mute,
                "solo": pad.solo,
                "chain_count": len(chains),
            })
        return {"pads": pads}

    # --- Return track devices ---

    @server.route("GET", "/live/returns/{return_id}/devices")
    def list_return_devices(return_id, body=None):
        track = _get_any_track("return", return_id)
        if track is None:
            return {"error": f"return track {return_id} not found"}
        return {
            "devices": [_device_info(i, d) for i, d in enumerate(track.devices)]
        }

    @server.route("GET", "/live/returns/{return_id}/devices/{device_id}/parameters")
    def list_return_device_params(return_id, device_id, body=None):
        track = _get_any_track("return", return_id)
        if track is None:
            return {"error": f"return track {return_id} not found"}
        devices = list(track.devices)
        if device_id < 0 or device_id >= len(devices):
            return {"error": f"device {device_id} not found on return track {return_id}"}
        dev = devices[device_id]
        return {
            "device": dev.name,
            "class_name": dev.class_name,
            "parameters": [_param_info(p) for p in dev.parameters],
        }

    @server.route("POST", "/live/returns/{return_id}/devices/{device_id}/parameters/batch")
    def set_return_device_params_batch(return_id, device_id, body=None):
        track = _get_any_track("return", return_id)
        if track is None:
            return {"error": f"return track {return_id} not found"}
        devices = list(track.devices)
        if device_id < 0 or device_id >= len(devices):
            return {"error": f"device {device_id} not found on return track {return_id}"}
        dev = devices[device_id]
        if not body or not isinstance(body, list):
            return {"error": "body must be a list of {name, value}"}
        params_by_name = {p.name: p for p in dev.parameters}
        results = []
        for item in body:
            name = item.get("name")
            value = item.get("value")
            if name in params_by_name and value is not None:
                params_by_name[name].value = float(value)
                results.append({"status": "ok", **_param_info(params_by_name[name])})
            else:
                results.append({"status": "error", "name": name, "error": "not found or missing value"})
        return {"results": results}

    @server.route("POST", "/live/returns/{return_id}/devices/{device_id}/parameters/{name}")
    def set_return_device_param(return_id, device_id, name, body=None):
        track = _get_any_track("return", return_id)
        if track is None:
            return {"error": f"return track {return_id} not found"}
        devices = list(track.devices)
        if device_id < 0 or device_id >= len(devices):
            return {"error": f"device {device_id} not found on return track {return_id}"}
        dev = devices[device_id]
        value = body.get("value") if body else None
        if value is None:
            return {"error": "missing 'value'"}
        for param in dev.parameters:
            if param.name == name:
                param.value = float(value)
                return {"status": "ok", **_param_info(param)}
        return {"error": f"parameter '{name}' not found"}

    # --- Load device from browser ---

    @server.route("POST", "/live/tracks/{track_id}/devices/load")
    def load_device(track_id, body=None):
        import Live
        name = (body or {}).get("name", "").strip()
        uri = (body or {}).get("uri", "").strip()
        if not name and not uri:
            return {"error": "missing 'name' or 'uri'"}
        song = util.song()
        track = _get_track(track_id)
        if track is None:
            return {"error": f"track {track_id} not found"}
        song.view.selected_track = track
        app = Live.Application.get_application()
        browser = app.browser
        search_order = [
            browser.instruments,
            browser.audio_effects,
            browser.midi_effects,
            browser.drums,
            browser.plugins,
            browser.max_for_live,
        ]
        def _matches(item):
            if uri:
                return item.uri == uri
            return item.name.lower() == name.lower()
        def _bfs(root, max_depth=3):
            from collections import deque
            queue = deque([(root, 0)])
            while queue:
                item, depth = queue.popleft()
                try:
                    if item.is_loadable and _matches(item):
                        return item
                except Exception:
                    pass
                if depth < max_depth:
                    try:
                        for child in item.children:
                            queue.append((child, depth + 1))
                    except Exception:
                        pass
            return None
        found = None
        for root in search_order:
            found = _bfs(root)
            if found:
                break
        if found is None:
            return {"error": f"device '{name or uri}' not found in browser"}
        before = len(list(track.devices))
        try:
            browser.load_item(found)
        except Exception as e:
            return {"error": f"load_item failed: {e}"}
        after = len(list(track.devices))
        if after <= before:
            return {"error": "load completed but no device was added — wrong track type?"}
        new_device = list(track.devices)[after - 1]
        return {"status": "ok", "device": _device_info(after - 1, new_device)}

    @server.route("POST", "/live/tracks/{track_id}/devices/preset")
    def load_preset(track_id, body=None):
        import Live
        path = (body or {}).get("path", "").strip()
        if not path:
            return {"error": "missing 'path'"}
        song = util.song()
        track = _get_track(track_id)
        if track is None:
            return {"error": f"track {track_id} not found"}
        song.view.selected_track = track
        app = Live.Application.get_application()
        browser = app.browser
        search_name = path.lower()
        search_order = [
            browser.user_library,
            browser.user_folders,
            browser.instruments,
            browser.audio_effects,
            browser.midi_effects,
            browser.drums,
            browser.packs,
        ]
        def _matches(item):
            n = item.name.lower()
            return n == search_name or n == search_name.rsplit(".", 1)[0].lower()
        def _bfs(root, max_depth=5):
            from collections import deque
            queue = deque([(root, 0)])
            while queue:
                item, depth = queue.popleft()
                try:
                    if item.is_loadable and _matches(item):
                        return item
                except Exception:
                    pass
                if depth < max_depth:
                    try:
                        for child in item.children:
                            queue.append((child, depth + 1))
                    except Exception:
                        pass
            return None
        found = None
        for root in search_order:
            try:
                found = _bfs(root)
            except Exception:
                pass
            if found:
                break
        if found is None:
            return {"error": f"preset '{path}' not found in browser"}
        before = len(list(track.devices))
        try:
            browser.load_item(found)
        except Exception as e:
            return {"error": f"load_item failed: {e}"}
        after = len(list(track.devices))
        if after <= before:
            return {"error": "load completed but no device was added"}
        new_device = list(track.devices)[after - 1]
        return {"status": "ok", "device": _device_info(after - 1, new_device)}

    @server.route("POST", "/live/tracks/{track_id}/devices/{device_id}/drum_pads/{pad_note}/sample")
    def add_drum_pad_sample(track_id, device_id, pad_note, body=None):
        import Live
        path = (body or {}).get("path", "").strip()
        if not path:
            return {"error": "missing 'path'"}
        _, device = _get_device(track_id, device_id)
        if device is None:
            return {"error": f"device {device_id} not found on track {track_id}"}
        if not device.can_have_drum_pads:
            return {"error": f"device '{device.name}' does not have drum pads"}
        pad = next((p for p in device.drum_pads if p.note == pad_note), None)
        if pad is None:
            return {"error": f"pad note {pad_note} not found"}
        track = _get_track(track_id)
        song = util.song()
        song.view.selected_track = track
        app = Live.Application.get_application()
        browser = app.browser
        filename = path.split("/")[-1].lower()
        def _matches(item):
            return item.name.lower() == filename or item.name.lower() == filename.rsplit(".", 1)[0].lower()
        def _bfs(root, max_depth=5):
            from collections import deque
            queue = deque([(root, 0)])
            while queue:
                item, depth = queue.popleft()
                try:
                    if item.is_loadable and _matches(item):
                        return item
                except Exception:
                    pass
                if depth < max_depth:
                    try:
                        for child in item.children:
                            queue.append((child, depth + 1))
                    except Exception:
                        pass
            return None
        found = None
        for root in [browser.user_library, browser.user_folders, browser.samples, browser.packs]:
            try:
                found = _bfs(root)
            except Exception:
                pass
            if found:
                break
        if found is None:
            return {"error": f"sample '{path}' not found in browser"}
        # Select the pad's chain in the view so load_item targets this pad
        try:
            song.view.selected_track = track
            device.view.selected_drum_pad = pad
        except Exception:
            pass
        chains_before = len(list(pad.chains))
        try:
            browser.load_item(found)
        except Exception as e:
            return {"error": f"load_item failed: {e}"}
        chains_after = len(list(pad.chains))
        if chains_after <= chains_before and chains_after == 0:
            return {"error": "load completed but no sample was added to pad"}
        return {
            "status": "ok",
            "pad_note": pad_note,
            "pad_name": pad.name,
            "sample": path,
        }

    # --- Device management ---

    @server.route("POST", "/live/tracks/{track_id}/devices/{device_id}/duplicate")
    def duplicate_device(track_id, device_id, body=None):
        track = _get_track(track_id)
        if track is None:
            return {"error": f"track {track_id} not found"}
        devices = list(track.devices)
        if device_id < 0 or device_id >= len(devices):
            return {"error": f"device {device_id} not found on track {track_id}"}
        track.duplicate_device(device_id)
        new_devices = list(track.devices)
        return {"status": "ok", "device_count": len(new_devices)}

    @server.route("POST", "/live/tracks/{track_id}/devices/{device_id}/delete")
    def delete_device(track_id, device_id, body=None):
        track = _get_track(track_id)
        if track is None:
            return {"error": f"track {track_id} not found"}
        devices = list(track.devices)
        if device_id < 0 or device_id >= len(devices):
            return {"error": f"device {device_id} not found on track {track_id}"}
        track.delete_device(device_id)
        return {"status": "ok", "device_count": len(list(track.devices))}

    @server.route("POST", "/live/song/move_device")
    def move_device(body=None):
        from_track_id = (body or {}).get("from_track_id")
        device_id = (body or {}).get("device_id")
        to_track_id = (body or {}).get("to_track_id")
        to_device_id = (body or {}).get("to_device_id", 0)
        if from_track_id is None or device_id is None or to_track_id is None:
            return {"error": "missing 'from_track_id', 'device_id', or 'to_track_id'"}
        song = util.song()
        tracks = list(song.tracks)
        if from_track_id < 0 or from_track_id >= len(tracks):
            return {"error": f"source track {from_track_id} not found"}
        if to_track_id < 0 or to_track_id >= len(tracks):
            return {"error": f"destination track {to_track_id} not found"}
        from_devices = list(tracks[from_track_id].devices)
        if device_id < 0 or device_id >= len(from_devices):
            return {"error": f"device {device_id} not found on track {from_track_id}"}
        song.move_device(from_devices[device_id], tracks[to_track_id], to_device_id)
        return {"status": "ok"}

    # --- Master track devices ---

    @server.route("GET", "/live/master/devices")
    def list_master_devices(body=None):
        master = util.song().master_track
        return {
            "devices": [_device_info(i, d) for i, d in enumerate(master.devices)]
        }

    @server.route("GET", "/live/master/devices/{device_id}/parameters")
    def list_master_device_params(device_id, body=None):
        master = util.song().master_track
        devices = list(master.devices)
        if device_id < 0 or device_id >= len(devices):
            return {"error": f"device {device_id} not found on master track"}
        dev = devices[device_id]
        return {
            "device": dev.name,
            "class_name": dev.class_name,
            "parameters": [_param_info(p) for p in dev.parameters],
        }

    @server.route("POST", "/live/master/devices/{device_id}/parameters/batch")
    def set_master_device_params_batch(device_id, body=None):
        master = util.song().master_track
        devices = list(master.devices)
        if device_id < 0 or device_id >= len(devices):
            return {"error": f"device {device_id} not found on master track"}
        dev = devices[device_id]
        if not body or not isinstance(body, list):
            return {"error": "body must be a list of {name, value}"}
        params_by_name = {p.name: p for p in dev.parameters}
        results = []
        for item in body:
            name = item.get("name")
            value = item.get("value")
            if name in params_by_name and value is not None:
                params_by_name[name].value = float(value)
                results.append({"status": "ok", **_param_info(params_by_name[name])})
            else:
                results.append({"status": "error", "name": name, "error": "not found or missing value"})
        return {"results": results}

    @server.route("POST", "/live/master/devices/{device_id}/parameters/{name}")
    def set_master_device_param(device_id, name, body=None):
        master = util.song().master_track
        devices = list(master.devices)
        if device_id < 0 or device_id >= len(devices):
            return {"error": f"device {device_id} not found on master track"}
        dev = devices[device_id]
        value = body.get("value") if body else None
        if value is None:
            return {"error": "missing 'value'"}
        for param in dev.parameters:
            if param.name == name:
                param.value = float(value)
                return {"status": "ok", **_param_info(param)}
        return {"error": f"parameter '{name}' not found"}
