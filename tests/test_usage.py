"""Tests for usage commands."""

import json
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from supertone_cli.cli import app
from supertone_cli.errors import APIError
from supertone_cli.models import Usage

runner = CliRunner()

_MOCK_USAGE = Usage(plan="pro", used=100, remaining=900)


def test_usage_balance_human_readable():
    """usage balance displays Plan, Used, Remaining."""
    with patch(
        "supertone_cli.commands.usage.get_usage",
        return_value=_MOCK_USAGE,
    ):
        result = runner.invoke(app, ["usage", "balance"])
    assert result.exit_code == 0
    assert "pro" in result.output
    assert "100" in result.output
    assert "900" in result.output


def test_usage_balance_format_json():
    """--format json produces valid JSON."""
    with patch(
        "supertone_cli.commands.usage.get_usage",
        return_value=_MOCK_USAGE,
    ):
        result = runner.invoke(app, ["usage", "balance", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["plan"] == "pro"
    assert data["used"] == 100
    assert data["remaining"] == 900


def test_usage_balance_api_error():
    """API error results in non-zero exit."""
    with patch(
        "supertone_cli.commands.usage.get_usage",
        side_effect=APIError("server down"),
    ):
        result = runner.invoke(app, ["usage", "balance"])
    assert result.exit_code != 0


# ── usage analytics ──────────────────────────────────────────────────


_MOCK_ANALYTICS = [
    {
        "period_start": "2026-04-01T00:00:00Z",
        "period_end": "2026-04-02T00:00:00Z",
        "minutes_used": 12.34,
        "voice_id": "v1",
        "voice_name": "Voice1",
        "model": "sona_speech_2",
    }
]


def test_usage_analytics_table():
    """usage analytics renders a table for a date range."""
    with patch(
        "supertone_cli.client.get_usage_analytics",
        return_value=_MOCK_ANALYTICS,
    ):
        result = runner.invoke(
            app,
            ["usage", "analytics", "--start", "2026-04-01", "--end", "2026-04-30"],
        )
    assert result.exit_code == 0


def test_usage_analytics_json():
    """usage analytics --format json returns the raw list."""
    with patch(
        "supertone_cli.client.get_usage_analytics",
        return_value=_MOCK_ANALYTICS,
    ):
        result = runner.invoke(
            app,
            [
                "usage",
                "analytics",
                "--start",
                "2026-04-01",
                "--end",
                "2026-04-30",
                "--format",
                "json",
            ],
        )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert data[0]["minutes_used"] == 12.34


def test_usage_analytics_empty():
    """usage analytics with no data prints a friendly message."""
    with patch(
        "supertone_cli.client.get_usage_analytics",
        return_value=[],
    ):
        result = runner.invoke(
            app,
            ["usage", "analytics", "--start", "2026-04-01", "--end", "2026-04-02"],
        )
    assert result.exit_code == 0
    assert "No usage data" in result.output


# ── usage analytics date serialization (ISSUE-029) ───────────────────


def _build_analytics_mock_client():
    """Build a MagicMock client whose get_usage returns a parseable shape."""
    mock_client = MagicMock()
    mock_bucket = MagicMock()
    mock_bucket.starting_at = "2026-06-01"
    mock_bucket.ending_at = "2026-06-02"
    mock_result = MagicMock()
    mock_result.minutes_used = 5.5
    mock_result.voice_id = "v1"
    mock_result.voice_name = "Voice1"
    mock_result.model = "sona_speech_2"
    mock_bucket.results = [mock_result]
    mock_response = MagicMock()
    mock_response.data = [mock_bucket]
    mock_client.usage.get_usage.return_value = mock_response
    return mock_client


def test_analytics_date_only_start_converts_to_iso():
    """A date-only start is forwarded to the SDK as start-of-day ISO datetime."""
    from supertone_cli.client import get_usage_analytics

    mock_client = _build_analytics_mock_client()
    with patch("supertone_cli.client.get_client", return_value=mock_client):
        get_usage_analytics("2026-06-01", "2026-06-15", "day")

    kwargs = mock_client.usage.get_usage.call_args.kwargs
    assert kwargs["start_time"] == "2026-06-01T00:00:00Z"


def test_analytics_date_only_end_converts_to_iso():
    """A date-only end is forwarded to the SDK as end-of-day ISO datetime."""
    from supertone_cli.client import get_usage_analytics

    mock_client = _build_analytics_mock_client()
    with patch("supertone_cli.client.get_client", return_value=mock_client):
        get_usage_analytics("2026-06-01", "2026-06-15", "day")

    kwargs = mock_client.usage.get_usage.call_args.kwargs
    assert kwargs["end_time"] == "2026-06-15T23:59:59Z"


def test_analytics_full_datetime_passed_through_unchanged():
    """A value already containing a 'T' is forwarded unchanged."""
    from supertone_cli.client import get_usage_analytics

    mock_client = _build_analytics_mock_client()
    with patch("supertone_cli.client.get_client", return_value=mock_client):
        get_usage_analytics("2026-06-01T08:30:00Z", "2026-06-15T19:45:00Z", "day")

    kwargs = mock_client.usage.get_usage.call_args.kwargs
    assert kwargs["start_time"] == "2026-06-01T08:30:00Z"
    assert kwargs["end_time"] == "2026-06-15T19:45:00Z"


def test_usage_analytics_date_range_cli_exits_zero():
    """CLI analytics with plain dates exits 0 with the SDK mocked."""
    mock_client = _build_analytics_mock_client()
    with patch("supertone_cli.client.get_client", return_value=mock_client):
        result = runner.invoke(
            app,
            ["usage", "analytics", "--start", "2026-06-01", "--end", "2026-06-15"],
        )
    assert result.exit_code == 0


# ── usage voices ─────────────────────────────────────────────────────


_MOCK_VOICE_USAGE = [
    {
        "date": "2026-04-01",
        "voice_id": "v1",
        "name": "Voice1",
        "minutes_used": 5.5,
        "model": "sona_speech_2",
        "language": "ko",
    }
]


def test_usage_voices_table():
    """usage voices renders per-voice breakdown as table."""
    with patch(
        "supertone_cli.client.get_voice_usage",
        return_value=_MOCK_VOICE_USAGE,
    ):
        result = runner.invoke(
            app,
            ["usage", "voices", "--start", "2026-04-01", "--end", "2026-04-30"],
        )
    assert result.exit_code == 0


def test_usage_voices_json():
    """usage voices --format json returns the raw list."""
    with patch(
        "supertone_cli.client.get_voice_usage",
        return_value=_MOCK_VOICE_USAGE,
    ):
        result = runner.invoke(
            app,
            [
                "usage",
                "voices",
                "--start",
                "2026-04-01",
                "--end",
                "2026-04-30",
                "--format",
                "json",
            ],
        )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data[0]["voice_id"] == "v1"
