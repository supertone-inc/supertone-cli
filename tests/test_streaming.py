"""Tests for ISSUE-013: streaming TTS playback."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from supertone_cli.cli import app
from supertone_cli.errors import InputError

runner = CliRunner()


def test_stream_calls_stream_speech():
    """--stream calls client.stream_speech."""
    mock_chunks = [b"chunk1", b"chunk2"]
    mock_sd = MagicMock()

    with (
        patch(
            "supertone_cli.client.stream_speech",
            return_value=iter(mock_chunks),
        ),
        patch.dict("sys.modules", {"sounddevice": mock_sd}),
    ):
        result = runner.invoke(
            app,
            [
                "tts",
                "Hello",
                "--voice",
                "v1",
                "--stream",
                "--model",
                "sona_speech_1",
            ],
        )
    assert result.exit_code == 0


def test_stream_missing_sounddevice():
    """Missing sounddevice raises InputError."""
    with patch.dict("sys.modules", {"sounddevice": None}):
        result = runner.invoke(
            app,
            [
                "tts",
                "Hello",
                "--voice",
                "v1",
                "--stream",
                "--model",
                "sona_speech_1",
            ],
        )
    assert result.exit_code != 0
    assert isinstance(result.exception, InputError)


def test_stream_defaults_to_sona_speech_1():
    """--stream without -m auto-selects sona_speech_1 (ISSUE-031)."""
    mock_sd = MagicMock()
    mock_stream = MagicMock(return_value=iter([b"chunk1"]))

    with (
        patch("supertone_cli.client.stream_speech", mock_stream),
        patch.dict("sys.modules", {"sounddevice": mock_sd}),
    ):
        result = runner.invoke(
            app,
            ["tts", "Hello", "--voice", "v1", "--stream"],
        )
    assert result.exit_code == 0
    assert mock_stream.call_args.kwargs["model"] == "sona_speech_1"


def test_stream_default_overrides_config_default_model():
    """--stream without -m picks sona_speech_1 even when config default_model
    is a non-streaming model (the load-bearing guarantee of ISSUE-031)."""
    mock_sd = MagicMock()
    mock_stream = MagicMock(return_value=iter([b"chunk1"]))

    def fake_default(key):
        return "sona_speech_2" if key == "default_model" else None

    with (
        patch("supertone_cli.client.stream_speech", mock_stream),
        patch("supertone_cli.commands.tts.get_default", side_effect=fake_default),
        patch.dict("sys.modules", {"sounddevice": mock_sd}),
    ):
        result = runner.invoke(
            app,
            ["tts", "Hello", "--voice", "v1", "--stream"],
        )
    assert result.exit_code == 0
    assert mock_stream.call_args.kwargs["model"] == "sona_speech_1"


def test_stream_explicit_incompatible_model_still_errors():
    """Explicit -m with a non-streaming model is still rejected."""
    mock_sd = MagicMock()
    with patch.dict("sys.modules", {"sounddevice": mock_sd}):
        result = runner.invoke(
            app,
            ["tts", "Hello", "--voice", "v1", "--stream", "--model", "sona_speech_2"],
        )
    assert result.exit_code != 0
    assert isinstance(result.exception, InputError)
    assert "Streaming requires sona_speech_1" in str(result.exception)


def test_stream_with_file_save(tmp_path):
    """--stream + --output saves to file too."""
    mock_chunks = [b"chunk1", b"chunk2"]
    mock_sd = MagicMock()
    out = tmp_path / "out.wav"

    with (
        patch(
            "supertone_cli.client.stream_speech",
            return_value=iter(mock_chunks),
        ),
        patch.dict("sys.modules", {"sounddevice": mock_sd}),
    ):
        result = runner.invoke(
            app,
            [
                "tts",
                "Hello",
                "--voice",
                "v1",
                "--stream",
                "--model",
                "sona_speech_1",
                "--output",
                str(out),
            ],
        )
    assert result.exit_code == 0
    assert out.exists()
    assert out.read_bytes() == b"chunk1chunk2"
