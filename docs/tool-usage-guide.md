# Tool Usage Guide

How to use the ableton-mcp tools correctly, especially when working with device parameters.

---

## Key concepts

**All IDs are 0-based integers** obtained from list calls — never hardcode them.

**Parameter values are raw numbers** in `[min, max]` range, not display strings.
`list_parameters` returns `"display": "2.00 kHz"` for human reference only — pass the numeric `value`, not the string.

**Volume scale** used everywhere (tracks, returns, master): `0.0` = silence, `0.85` = 0 dB, `1.0` = +6 dB.

**Beats, not seconds** — all time values (clip length, note position, loop start/end, transport position) are in beats.
In 4/4: 1 beat = 1 quarter note, 4 beats = 1 bar, 16 beats = 4 bars.

---

## Standard workflow for changing a device parameter

```
1. list_tracks()
   → find track_id by name

2. list_devices(track_id)
   → find device_id by name or class_name

3. list_parameters(track_id, device_id)
   → find parameter by name, note its min/max range

4. set_parameters_batch(track_id, device_id, [...])   ← preferred for 2+ params
   OR set_parameter(track_id, device_id, name, value) ← for a single param
```

### Example — set Wavetable filter to 500 Hz with high resonance

```
list_tracks()
→ {"tracks": [{"id": 0, "name": "Bass", "type": "midi"}, ...]}

list_devices(track_id=0)
→ {"devices": [{"id": 0, "name": "Wavetable", "class_name": "InstrumentVector", ...}]}

list_parameters(track_id=0, device_id=0)
→ {"parameters": [
    {"name": "Filter Freq",  "value": 20000.0, "display": "20.0 kHz", "min": 20.0,  "max": 20000.0},
    {"name": "Filter Res",   "value": 0.0,     "display": "0.00 %",   "min": 0.0,   "max": 1.0},
    ...
  ]}

set_parameters_batch(track_id=0, device_id=0, parameters=[
    {"name": "Filter Freq", "value": 500.0},
    {"name": "Filter Res",  "value": 0.75}
])
```

---

## Ableton internal class names

GUI name → `class_name` returned by `list_devices`:

| GUI name  | class_name          |
|-----------|---------------------|
| Wavetable | `InstrumentVector`  |
| Analog    | `UltraAnalog`       |
| Operator  | `Operator`          |
| Simpler   | `OriginalSimpler`   |
| Sampler   | `MultiSampler`      |
| Impulse   | `InstrumentImpulse` |
| Drum Rack | `DrumGroupDevice`   |

---

## Common mistakes

**Wrong — passing display string as value:**
```
set_parameter(0, 0, "Filter Freq", "2.00 kHz")  ✗ — string, not a number
```

**Wrong — guessing parameter name:**
```
set_parameter(0, 0, "filter frequency", 500.0)  ✗ — name must match exactly
```

**Correct:**
```
# 1. Get the exact name from list_parameters first
# 2. Use the raw number within [min, max]
set_parameter(0, 0, "Filter Freq", 500.0)  ✓
```

---

## Devices inside racks (chains)

For instruments/effects inside an Instrument Rack or Audio Effect Rack, add two extra steps:

```
1. list_tracks()                                          → track_id
2. list_devices(track_id)                                 → device_id  (the rack itself)
3. list_chains(track_id, device_id)                       → chain_id, chain_device_id
4. list_chain_device_parameters(track_id, device_id,
                                chain_id, chain_device_id) → parameter names and ranges
5. set_chain_device_parameters_batch(...)
```

---

## MIDI notes

`pitch` = MIDI note number (0–127):

| Note | Number |
|------|--------|
| C4 (middle C) | 60 |
| A4 (440 Hz)   | 69 |
| C1 (kick drum default) | 36 |
| D1 (snare default)     | 38 |

`duration` in beats: `1.0` = quarter note, `0.5` = eighth, `0.25` = sixteenth.

Notes are **added** to existing content — call `clear_clip` first if you want to replace.

### Example — 4-beat kick/snare pattern

```
create_midi_clip(track_id=0, length=4.0)
→ {"id": 0, ...}  ← clip_id

add_notes_to_clip(track_id=0, clip_id=0, notes=[
    {"pitch": 36, "time": 0.0, "duration": 0.25, "velocity": 100},  # kick beat 1
    {"pitch": 36, "time": 2.0, "duration": 0.25, "velocity": 100},  # kick beat 3
    {"pitch": 38, "time": 1.0, "duration": 0.25, "velocity": 90},   # snare beat 2
    {"pitch": 38, "time": 3.0, "duration": 0.25, "velocity": 90},   # snare beat 4
])
```

---

## Error handling

All tools return `{"error": "..."}` on failure. Common causes:

| Error | Fix |
|-------|-----|
| `parameter '...' not found` | Check exact spelling from `list_parameters` |
| `track N not found` | Re-run `list_tracks` — IDs shift after create/delete |
| `no empty clip slot` | Track has no free slots; duplicate track or use a different track |
| `cannot delete last scene` | At least one scene must always exist |
| `does not support chains` | Device is not a rack type |

---

## All available tools

### Transport & session

| Tool | Parameters | Description |
|------|-----------|-------------|
| `get_session_info` | — | Current transport state (BPM, playing, position, etc.) |
| `get_full_state` | — | Full session snapshot in one call |
| `play` | — | Start playback |
| `stop` | — | Stop playback |
| `record` | — | Toggle session record mode |
| `set_bpm` | `bpm` | Set tempo |
| `set_loop` | `enabled`, `start`, `length` | Set arrangement loop |
| `set_metronome` | `enabled` | Set or toggle metronome |
| `jump_to_position` | `position` | Move playhead (beats) |
| `undo` | — | Undo last action |
| `redo` | — | Redo last undone action |

### Tracks

| Tool | Parameters | Description |
|------|-----------|-------------|
| `list_tracks` | — | List all MIDI/audio tracks |
| `get_track` | `track_id` | Details for one track including sends |
| `create_midi_track` | `index=-1` | Create a new MIDI track |
| `create_audio_track` | `index=-1` | Create a new audio track |
| `delete_track` | `track_id` | Delete a track (use `undo` to recover) |
| `duplicate_track` | `track_id` | Duplicate a track |
| `rename_track` | `track_id`, `name` | Rename a track |
| `select_track` | `track_id` | Select/highlight a track in the GUI |
| `set_track_volume` | `track_id`, `value` | Volume (0.85 = 0 dB) |
| `set_track_pan` | `track_id`, `value` | Pan (−1.0 left … 1.0 right) |
| `set_track_arm` | `track_id`, `armed` | Arm/disarm for recording |
| `set_track_solo` | `track_id`, `solo` | Solo on/off |
| `set_track_mute` | `track_id`, `mute` | Mute on/off |
| `set_track_send` | `track_id`, `send_index`, `value` | Set a send level |
| `stop_track` | `track_id` | Stop all playing clips on a track |
| `get_playing_clips` | — | List currently playing clips |
| `get_armed_tracks` | — | List currently armed tracks |

### Clips

| Tool | Parameters | Description |
|------|-----------|-------------|
| `list_clips` | `track_id` | List clips on a track |
| `get_clip` | `track_id`, `clip_id` | Details for a clip slot |
| `create_midi_clip` | `track_id`, `length=4.0`, `name=""` | Create empty MIDI clip |
| `duplicate_clip` | `track_id`, `clip_id` | Duplicate to next empty slot |
| `duplicate_loop` | `track_id`, `clip_id` | Double loop content (clip × 2) |
| `rename_clip` | `track_id`, `clip_id`, `name` | Rename a clip |
| `set_clip_color` | `track_id`, `clip_id`, `color_index` | Set clip color (0–69) |
| `set_clip_loop` | `track_id`, `clip_id`, `start`, `end`, `enabled` | Set clip loop points |
| `extend_clip_loop` | `track_id`, `clip_id`, `bars=1` | Extend loop end by N bars |
| `fire_clip` | `track_id`, `clip_id` | Launch a clip |
| `stop_clip` | `track_id`, `clip_id` | Stop a clip |

### MIDI notes

| Tool | Parameters | Description |
|------|-----------|-------------|
| `get_clip_notes` | `track_id`, `clip_id` | Get all notes from a clip |
| `add_notes_to_clip` | `track_id`, `clip_id`, `notes` | Add notes (pitch, time, duration, velocity) |
| `clear_clip` | `track_id`, `clip_id` | Remove all notes from a clip |
| `delete_notes_by_pitch` | `track_id`, `clip_id`, `pitches` | Delete notes by pitch list |
| `delete_notes_in_range` | `track_id`, `clip_id`, `start`, `end` | Delete notes in beat range |

### Devices — regular tracks

| Tool | Parameters | Description |
|------|-----------|-------------|
| `list_devices` | `track_id` | List devices on a track |
| `list_parameters` | `track_id`, `device_id` | List device parameters |
| `set_parameter` | `track_id`, `device_id`, `name`, `value` | Set one parameter |
| `set_parameters_batch` | `track_id`, `device_id`, `parameters` | Set multiple parameters at once |
| `set_device_enabled` | `track_id`, `device_id`, `enabled` | Bypass/enable a device |

### Devices — racks & chains

| Tool | Parameters | Description |
|------|-----------|-------------|
| `list_chains` | `track_id`, `device_id` | List chains in a rack |
| `list_chain_device_parameters` | `track_id`, `device_id`, `chain_id`, `chain_device_id` | List parameters of a device inside a chain |
| `set_chain_device_parameter` | `track_id`, `device_id`, `chain_id`, `chain_device_id`, `name`, `value` | Set one chain device parameter |
| `set_chain_device_parameters_batch` | `track_id`, `device_id`, `chain_id`, `chain_device_id`, `parameters` | Set multiple chain device parameters |
| `list_drum_pads` | `track_id`, `device_id` | List drum pads in a Drum Rack |

### Return tracks

| Tool | Parameters | Description |
|------|-----------|-------------|
| `list_returns` | — | List all return tracks |
| `get_return` | `return_id` | Return track details |
| `set_return_volume` | `return_id`, `value` | Volume (0.85 = 0 dB) |
| `set_return_pan` | `return_id`, `value` | Pan |
| `list_return_devices` | `return_id` | List devices on a return |
| `list_return_device_parameters` | `return_id`, `device_id` | List parameters |
| `set_return_device_parameter` | `return_id`, `device_id`, `name`, `value` | Set one parameter |

### Master track

| Tool | Parameters | Description |
|------|-----------|-------------|
| `get_master` | — | Master track info |
| `set_master_volume` | `value` | Volume (0.85 = 0 dB) |
| `list_master_devices` | — | List master track devices |
| `list_master_device_parameters` | `device_id` | List parameters |
| `set_master_device_parameter` | `device_id`, `name`, `value` | Set one parameter |

### Scenes

| Tool | Parameters | Description |
|------|-----------|-------------|
| `list_scenes` | — | List all scenes |
| `create_scene` | `name=""` | Create a new scene |
| `delete_scene` | `scene_id` | Delete a scene |
| `duplicate_scene` | `scene_id` | Duplicate a scene |
| `rename_scene` | `scene_id`, `name` | Rename a scene |
| `fire_scene` | `scene_id` | Launch all clips in a scene |
| `select_scene` | `scene_id` | Select/highlight a scene in the GUI |

### Arrangement View

| Tool | Parameters | Description |
|------|-----------|-------------|
| `list_arrangement_clips` | `track_id` | List all clips on a track in Arrangement View |
| `create_arrangement_clip` | `track_id`, `start_time`, `length=4.0`, `name=""` | Create a MIDI clip at a position (beats) |
| `delete_arrangement_clip` | `track_id`, `start_time` | Delete an arrangement clip |
| `move_arrangement_clip` | `track_id`, `start_time`, `position` | Move clip to a new timeline position |
| `resize_arrangement_clip` | `track_id`, `start_time`, `end_time`, `new_start_time` | Resize clip by adjusting start/end |
| `set_arrangement_clip_loop` | `track_id`, `start_time`, `looping`, `loop_start`, `loop_end` | Set loop region on an arrangement clip |
| `rename_arrangement_clip` | `track_id`, `start_time`, `name` | Rename an arrangement clip |
| `set_arrangement_clip_mute` | `track_id`, `start_time`, `muted` | Mute/unmute an arrangement clip |
| `duplicate_clip_to_arrangement` | `track_id`, `clip_id`, `start_time` | Copy a Session View clip to Arrangement |
| `set_arrangement_overdub` | `enabled` | Enable/disable arrangement overdub (omit to toggle) |
| `back_to_arranger` | — | Return playback control to Arrangement View |

### Clip envelopes (automation)

| Tool | Parameters | Description |
|------|-----------|-------------|
| `list_clip_envelopes` | `track_id`, `clip_id` | List automation envelopes in a Session clip |
| `get_clip_envelope_events` | `track_id`, `clip_id`, `device_id`, `param_name` | Get all automation points from an envelope |
| `insert_clip_envelope_step` | `track_id`, `clip_id`, `device_id`, `param_name`, `time`, `value`, `duration=0.0` | Insert an automation point |
| `delete_clip_envelope_range` | `track_id`, `clip_id`, `device_id`, `param_name`, `from_time`, `to_time` | Delete automation points in a range |

### Song & transport extras

| Tool | Parameters | Description |
|------|-----------|-------------|
| `tap_tempo` | — | Tap to set BPM |
| `jump_by` | `beats` | Jump playhead forward/backward by N beats |
| `scrub_by` | `beats` | Scrub playhead by N beats |
| `jump_to_next_cue` | — | Jump to next cue point |
| `jump_to_prev_cue` | — | Jump to previous cue point |
| `get_cue_points` | — | List all cue points |
| `set_or_delete_cue` | `name`, `delete=false` | Set or delete a cue at the current position |
| `get_scale` | — | Get current scale settings |
| `set_scale` | `root_note`, `name`, `enabled` | Set scale (root 0–11, name e.g. "Minor") |
| `capture_midi` | — | Capture MIDI from the buffer into a clip |
| `capture_and_insert_scene` | — | Capture playing clips as a new scene |
| `trigger_session_record` | — | Trigger session recording |
| `re_enable_automation` | — | Re-enable automation after manual override |
| `get_version` | — | Get Ableton Live version info |
| `describe_session_structure` | — | AI-friendly session analysis (track roles, genre guess, energy) |

### Browser & loading devices

| Tool | Parameters | Description |
|------|-----------|-------------|
| `get_browser_info` | — | Browser categories and metadata |
| `browse_devices` | `category` | Browse device tree (instruments, effects, samples, etc.) |
| `load_device` | `track_id`, `device_name` | Load a device onto a track by name |
| `load_preset` | `track_id`, `preset_uri` | Load a preset from browser URI |
| `create_drum_rack` | `track_id` | Create a Drum Rack on a track |
| `add_drum_pad_sample` | `track_id`, `device_id`, `pad_note`, `sample_path` | Add a sample to a drum pad |
| `duplicate_device` | `track_id`, `device_id` | Duplicate a device |
| `delete_device` | `track_id`, `device_id` | Delete a device |
| `move_device` | `track_id`, `device_id`, `target_track_id`, `target_index` | Move device to another track |

### Extra clip operations

| Tool | Parameters | Description |
|------|-----------|-------------|
| `quantize_clip` | `track_id`, `clip_id`, `quantize_to=1.0`, `amount=1.0` | Quantize clip notes |
| `crop_clip` | `track_id`, `clip_id` | Crop clip to loop boundaries |
| `set_audio_clip_props` | `track_id`, `clip_id`, `pitch_coarse`, `pitch_fine`, `gain`, `warp_mode`, `warping` | Set audio clip properties |
| `set_clip_mute` | `track_id`, `clip_id`, `muted` | Mute/unmute a Session View clip |
| `set_clip_velocity_amount` | `track_id`, `clip_id`, `amount` | Set velocity randomization amount |
| `create_return_track` | — | Create a new return track |
