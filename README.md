# ableton-mcp

MCP server + Ableton Control Surface for controlling Ableton Live via Claude.

```
Claude (MCP client) ↔ ableton-mcp (Python MCP server) ↔ HTTP ↔ Control Surface ↔ Ableton Live
```

## Setup

### 1. Install the MCP server

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2. Install the Control Surface

Copy `ableton_http_bridge` into `Remote Scripts` direcotry in `User Library`:

```bash
cp -r control_surface/ableton_http_bridge  ~/Music/Ableton/User\ Library/Remote\ Scripts/
```

Then in Ableton: **Preferences → Link, Tempo & MIDI → Control Surface** → select `ableton_http_bridge`.

### 3. Configure Claude

Add to your MCP client config (replace `/absolute/path/to/ableton-mcp` with path to this repository):

```json
{
  "mcpServers": {
    "ableton": {
      "command": "/absolute/path/to/ableton-mcp/.venv/bin/ableton-mcp"
    }
  }
}
```

## Usage

Start Ableton Live with the Control Surface enabled, then use Claude with the MCP server to control it — set tempo, play/stop, manipulate clips, tweak device parameters, and more.

See [docs/tool-usage-guide.md](docs/tool-usage-guide.md) for a detailed guide on how to use the tools correctly, including workflows for device parameters, MIDI notes, and rack chains.

## Requirements

- Python 3.11+
- Ableton Live (with Control Surface support)
