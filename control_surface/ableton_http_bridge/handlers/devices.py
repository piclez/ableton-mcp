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
