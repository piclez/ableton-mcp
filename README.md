# ableton-mcp

Control Ableton Live with Claude. An MCP server + Ableton Control Surface that exposes the full Live API over HTTP, so an AI assistant can manipulate your session in real time.

```
Claude ↔ ableton-mcp (MCP server) ↔ HTTP ↔ Control Surface ↔ Ableton Live
```

## What you can do

- **Compose** — create clips, write MIDI notes, build drum patterns, arrange on the timeline
- **Sound design** — load instruments and effects, tweak every parameter by name, build rack chains
- **Mix** — set volumes, pans, sends, automate parameters with clip envelopes
- **Navigate** — play, stop, fire scenes, jump to cue points, control the transport
- **Explore** — browse the device library, load presets, add samples to drum pads

135+ tools covering tracks, clips, devices, scenes, arrangement view, and automation envelopes.

## Requirements

- Python 3.11+
- Ableton Live 11 or 12 (Suite or Standard with Control Surface support)

## Setup

### 1. Install the MCP server

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
```

### 2. Install the Control Surface

```bash
cp -r control_surface/ableton_http_bridge ~/Music/Ableton/User\ Library/Remote\ Scripts/
```

Then in Ableton: **Preferences → Link, Tempo & MIDI → Control Surface** → select `ableton_http_bridge`.

### 3. Configure Claude

Add to your MCP client config (e.g. `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "ableton": {
      "command": "/absolute/path/to/ableton-mcp/.venv/bin/ableton-mcp"
    }
  }
}
```

Replace `/absolute/path/to/ableton-mcp` with the actual path to this repository.

## Example

Here's what you can ask Claude:

> *"Create a 4-bar drum pattern on track 1 with a kick on beats 1 and 3, snare on 2 and 4, and a 16th-note hi-hat groove"*

> *"Load Wavetable on the Bass track, set the filter to 400 Hz with 60% resonance, and automate the cutoff to sweep from 200 Hz to 8 kHz over 8 bars"*

> *"Duplicate the current scene, rename it 'Chorus', and fire it"*

## Documentation

- [Tool usage guide](docs/tool-usage-guide.md) — workflows, parameter conventions, common mistakes, all 135+ tools

## Architecture

The Control Surface runs inside Ableton's embedded Python 3.11 (stdlib only, no pip). It starts a local HTTP server on port 8765 (override with `ABLETON_HTTP_PORT`) in a daemon thread; all Live API calls are scheduled back to the main thread via `_ControlSurface__component_guard`. The external MCP server communicates with it over HTTP using `httpx`.

## License

MIT
