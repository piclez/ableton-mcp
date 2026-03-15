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
