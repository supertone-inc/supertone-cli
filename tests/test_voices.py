"""Tests for ISSUE-008: voices list command."""

import json
from unittest.mock import patch

from typer.testing import CliRunner

from supertone_cli.cli import app
from supertone_cli.models import Voice

runner = CliRunner()

_MOCK_VOICES = [
    Voice(
        id="v1",
        name="Voice1",
        type="preset",
        languages=["ko", "en"],
        gender="male",
        age="adult",
        use_cases=["narration"],
    ),
    Voice(
        id="v2",
        name="Voice2",
        type="custom",
        languages=["ko"],
        gender="female",
        age="young",
        use_cases=[],
    ),
]


def test_voices_list_renders_table():
    """voices list displays a table."""
    with patch(
        "supertone_cli.commands.voices.list_voices",
        return_value=_MOCK_VOICES,
    ):
        result = runner.invoke(app, ["voices", "list"])
    assert result.exit_code == 0


def test_voices_list_type_preset():
    """--type preset filters to preset voices only."""
    with patch(
        "supertone_cli.commands.voices.list_voices",
        return_value=_MOCK_VOICES,
    ):
        result = runner.invoke(app, ["voices", "list", "--type", "preset"])
    assert result.exit_code == 0


def test_voices_list_type_custom():
    """--type custom calls list_custom_voices."""
    custom_voices = [
        Voice(
            id="v2",
            name="Voice2",
            type="custom",
            languages=["ko"],
            gender="female",
            age="young",
            use_cases=[],
        ),
    ]
    with patch(
        "supertone_cli.commands.voices.list_custom_voices",
        return_value=custom_voices,
    ):
        result = runner.invoke(app, ["voices", "list", "--type", "custom"])
    assert result.exit_code == 0


def test_voices_list_format_json():
    """--format json produces valid JSON array."""
    with patch(
        "supertone_cli.commands.voices.list_voices",
        return_value=_MOCK_VOICES,
    ):
        result = runner.invoke(app, ["voices", "list", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["id"] == "v1"


def test_voices_list_empty():
    """Empty voice list returns exit code 0."""
    with patch(
        "supertone_cli.commands.voices.list_voices",
        return_value=[],
    ):
        result = runner.invoke(app, ["voices", "list"])
    assert result.exit_code == 0


def test_voices_list_json_empty():
    """Empty voice list as JSON returns []."""
    with patch(
        "supertone_cli.commands.voices.list_voices",
        return_value=[],
    ):
        result = runner.invoke(app, ["voices", "list", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data == []


# ── voices get ───────────────────────────────────────────────────────


def test_voices_get_human_readable():
    """voices get prints Name/ID/Type/Languages."""
    voice = Voice(
        id="v1",
        name="Test Voice",
        type="preset",
        languages=["ko", "en"],
        gender="female",
        age="adult",
        use_cases=["narration"],
    )
    with patch("supertone_cli.client.get_voice", return_value=voice):
        result = runner.invoke(app, ["voices", "get", "v1"])
    assert result.exit_code == 0
    assert "Test Voice" in result.output
    assert "v1" in result.output
    assert "ko" in result.output


def test_voices_get_format_json():
    """voices get --format json produces valid JSON."""
    voice = Voice(id="v1", name="Test", type="preset", languages=["ko"])
    with patch("supertone_cli.client.get_voice", return_value=voice):
        result = runner.invoke(app, ["voices", "get", "v1", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["id"] == "v1"
    assert data["name"] == "Test"


def test_voices_get_custom_voice_human_readable():
    """voices get on a custom voice exits 0 and shows the custom type."""
    voice = Voice(
        id="c1",
        name="My Clone",
        type="custom",
        languages=["ko"],
        gender="female",
        age="young",
        use_cases=[],
    )
    with patch("supertone_cli.client.get_voice", return_value=voice):
        result = runner.invoke(app, ["voices", "get", "c1"])
    assert result.exit_code == 0
    assert "custom" in result.output


def test_voices_get_custom_voice_format_json():
    """voices get --format json on a custom voice reports type custom."""
    voice = Voice(id="c1", name="My Clone", type="custom", languages=["ko"])
    with patch("supertone_cli.client.get_voice", return_value=voice):
        result = runner.invoke(app, ["voices", "get", "c1", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["type"] == "custom"


# ── voices edit ──────────────────────────────────────────────────────


def test_voices_edit_name():
    """voices edit --name updates the voice."""
    from supertone_cli.models import CloneResult

    with patch(
        "supertone_cli.client.edit_custom_voice",
        return_value=CloneResult(voice_id="v1", name="Renamed"),
    ) as mock_edit:
        result = runner.invoke(app, ["voices", "edit", "v1", "--name", "Renamed"])
    assert result.exit_code == 0
    mock_edit.assert_called_once_with("v1", name="Renamed", description=None)


def test_voices_edit_requires_field():
    """voices edit with neither --name nor --description exits with error."""
    result = runner.invoke(app, ["voices", "edit", "v1"])
    assert result.exit_code != 0


def test_voices_edit_format_json():
    """voices edit --format json returns JSON result."""
    from supertone_cli.models import CloneResult

    with patch(
        "supertone_cli.client.edit_custom_voice",
        return_value=CloneResult(voice_id="v1", name="New"),
    ):
        result = runner.invoke(
            app, ["voices", "edit", "v1", "--name", "New", "--format", "json"]
        )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["voice_id"] == "v1"


# ── voices delete ────────────────────────────────────────────────────


def test_voices_delete_with_yes():
    """voices delete --yes skips confirmation."""
    with patch("supertone_cli.client.delete_custom_voice") as mock_delete:
        result = runner.invoke(app, ["voices", "delete", "v1", "--yes"])
    assert result.exit_code == 0
    mock_delete.assert_called_once_with("v1")


def test_voices_delete_confirmation_declined():
    """voices delete aborts when user declines confirmation."""
    with patch("supertone_cli.client.delete_custom_voice") as mock_delete:
        result = runner.invoke(app, ["voices", "delete", "v1"], input="n\n")
    assert result.exit_code != 0
    mock_delete.assert_not_called()
