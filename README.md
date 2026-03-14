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

Symlink (recommended — changes apply immediately):

```bash
ln -s "$(pwd)/control_surface/ableton_http_bridge" "~/Music/Ableton/User Library/Remote Scripts/"
```

Or copy manually:

```bash
cp -r control_surface/ableton_http_bridge "~/Music/Ableton/User Library/Remote Scripts/"
```

Then in Ableton: **Preferences → Link, Tempo & MIDI → Control Surface** → select `ableton_http_bridge`.

### 3. Configure Claude

Add to your MCP client config:

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

## Requirements

- Python 3.11+
- Ableton Live (with Control Surface support)
