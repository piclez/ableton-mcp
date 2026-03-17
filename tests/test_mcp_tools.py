"""Tests for MCP tool → HTTP endpoint mapping.

Each test verifies that a tool calls the correct HTTP method + URL
and passes the right parameters. Ableton Live is not needed.
"""

from unittest.mock import AsyncMock, patch

import pytest

import ableton_mcp.server as srv


@pytest.fixture(autouse=True)
def mock_client():
    """Replace the module-level client with a mock for all tests."""
    mock = AsyncMock()
    mock.get = AsyncMock(return_value={})
    mock.post = AsyncMock(return_value={})
    mock.delete = AsyncMock(return_value={})
    with patch.object(srv, "client", mock):
        yield mock


# --- Transport ---

@pytest.mark.anyio
async def test_get_session_info(mock_client):
    await srv.get_session_info()
    mock_client.get.assert_called_once_with("/live/transport")


@pytest.mark.anyio
async def test_set_bpm(mock_client):
    await srv.set_bpm(128.0)
    mock_client.post.assert_called_once_with("/live/transport/bpm", {"bpm": 128.0})


@pytest.mark.anyio
async def test_play(mock_client):
    await srv.play()
    mock_client.post.assert_called_once_with("/live/transport/play")


@pytest.mark.anyio
async def test_stop(mock_client):
    await srv.stop()
    mock_client.post.assert_called_once_with("/live/transport/stop")


# --- Tracks ---

@pytest.mark.anyio
async def test_list_tracks(mock_client):
    await srv.list_tracks()
    mock_client.get.assert_called_once_with("/live/tracks")


@pytest.mark.anyio
async def test_set_track_volume(mock_client):
    await srv.set_track_volume(2, 0.85)
    mock_client.post.assert_called_once_with("/live/tracks/2/volume", {"value": 0.85})


@pytest.mark.anyio
async def test_rename_track(mock_client):
    await srv.rename_track(0, "Kick")
    mock_client.post.assert_called_once_with("/live/tracks/0/name", {"name": "Kick"})


@pytest.mark.anyio
async def test_delete_track(mock_client):
    await srv.delete_track(3)
    mock_client.delete.assert_called_once_with("/live/tracks/3")


# --- Clips ---

@pytest.mark.anyio
async def test_create_midi_clip(mock_client):
    await srv.create_midi_clip(1, length=8.0, name="Loop")
    mock_client.post.assert_called_once_with(
        "/live/tracks/1/clips/create", {"length": 8.0, "name": "Loop"}
    )


@pytest.mark.anyio
async def test_add_notes_to_clip(mock_client):
    notes = [{"pitch": 36, "time": 0.0, "duration": 0.25, "velocity": 100}]
    await srv.add_notes_to_clip(0, 0, notes)
    mock_client.post.assert_called_once_with("/live/tracks/0/clips/0/notes", notes)


@pytest.mark.anyio
async def test_delete_track_via_delete_method(mock_client):
    await srv.delete_track(5)
    mock_client.delete.assert_called_once_with("/live/tracks/5")


# --- Devices ---

@pytest.mark.anyio
async def test_list_parameters(mock_client):
    await srv.list_parameters(1, 0)
    mock_client.get.assert_called_once_with("/live/tracks/1/devices/0/parameters")


@pytest.mark.anyio
async def test_set_parameter(mock_client):
    await srv.set_parameter(0, 0, "Filter Freq", 500.0)
    mock_client.post.assert_called_once_with(
        "/live/tracks/0/devices/0/parameters/Filter Freq", {"value": 500.0}
    )


@pytest.mark.anyio
async def test_set_parameters_batch(mock_client):
    params = [{"name": "Filter Freq", "value": 500.0}, {"name": "Filter Res", "value": 0.5}]
    await srv.set_parameters_batch(0, 0, params)
    mock_client.post.assert_called_once_with(
        "/live/tracks/0/devices/0/parameters/batch", params
    )


# --- Arrangement ---

@pytest.mark.anyio
async def test_create_arrangement_clip(mock_client):
    await srv.create_arrangement_clip(0, 16.0, length=4.0, name="Verse")
    mock_client.post.assert_called_once_with(
        "/live/tracks/0/arrangement_clips/create",
        {"start_time": 16.0, "length": 4.0, "name": "Verse"},
    )


@pytest.mark.anyio
async def test_rename_arrangement_clip(mock_client):
    await srv.rename_arrangement_clip(0, 8.0, "Drop")
    mock_client.post.assert_called_once_with(
        "/live/tracks/0/arrangement_clips/8.0/name", {"name": "Drop"}
    )


@pytest.mark.anyio
async def test_set_arrangement_clip_mute(mock_client):
    await srv.set_arrangement_clip_mute(1, 4.0, True)
    mock_client.post.assert_called_once_with(
        "/live/tracks/1/arrangement_clips/4.0/mute", {"muted": True}
    )


@pytest.mark.anyio
async def test_delete_arrangement_clip(mock_client):
    await srv.delete_arrangement_clip(0, 8.0)
    mock_client.delete.assert_called_once_with("/live/tracks/0/arrangement_clips/8.0")


# --- Scenes ---

@pytest.mark.anyio
async def test_fire_scene(mock_client):
    await srv.fire_scene(2)
    mock_client.post.assert_called_once_with("/live/scenes/2/fire")


@pytest.mark.anyio
async def test_delete_scene(mock_client):
    await srv.delete_scene(1)
    mock_client.delete.assert_called_once_with("/live/scenes/1")
