"""Tests for SDK client wrapper and data models."""

from dataclasses import FrozenInstanceError
from unittest.mock import MagicMock, patch

import pytest

from supertone_cli.errors import APIError, AuthError

# ── Data model tests ─────────────────────────────────────────────────


def test_voice_is_frozen_dataclass():
    from supertone_cli.models import Voice

    v = Voice(
        id="v1",
        name="Test Voice",
        type="preset",
        languages=["ko", "en"],
        gender="female",
        age="young",
        use_cases=["narration"],
    )
    assert v.id == "v1"
    assert v.type == "preset"
    with pytest.raises(FrozenInstanceError):
        v.id = "v2"


def test_usage_is_frozen_dataclass():
    from supertone_cli.models import Usage

    u = Usage(plan="pro", used=100, remaining=900)
    assert u.plan == "pro"
    with pytest.raises(FrozenInstanceError):
        u.plan = "free"


def test_prediction_dataclass():
    from supertone_cli.models import Prediction

    p = Prediction(duration_seconds=3.2, estimated_credits=47)
    assert p.duration_seconds == 3.2


def test_clone_result_dataclass():
    from supertone_cli.models import CloneResult

    c = CloneResult(voice_id="clone-1", name="my-voice")
    assert c.voice_id == "clone-1"


def test_tts_result_dataclass():
    from supertone_cli.models import TTSResult

    t = TTSResult(
        output_file="out.wav",
        duration_seconds=2.5,
        voice_id="v1",
    )
    assert t.output_file == "out.wav"


def test_batch_result_dataclass():
    from supertone_cli.models import BatchResult

    b = BatchResult(succeeded=3, failed=1, total=4)
    assert b.total == 4


def test_batch_error_dataclass():
    from supertone_cli.models import BatchError

    e = BatchError(file="a.txt", error="API timeout")
    assert e.file == "a.txt"


# ── Client tests ─────────────────────────────────────────────────────


def test_get_client_with_no_api_key_raises_auth_error():
    from supertone_cli.client import get_client

    with (
        patch("supertone_cli.client._client", None),
        patch(
            "supertone_cli.client.get_api_key",
            return_value=None,
        ),
    ):
        with pytest.raises(AuthError):
            get_client()


def test_get_client_with_api_key_returns_client():
    from supertone_cli.client import get_client

    mock_sdk = MagicMock()
    mock_client = MagicMock()
    mock_sdk.Supertone.return_value = mock_client

    with (
        patch("supertone_cli.client._client", None),
        patch(
            "supertone_cli.client.get_api_key",
            return_value="sk-test",
        ),
        patch.dict("sys.modules", {"supertone": mock_sdk}),
    ):
        client = get_client()
        assert client is mock_client


def test_create_speech_returns_bytes():
    from supertone_cli.client import create_speech

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.result = b"audio-bytes"
    mock_client.text_to_speech.create_speech.return_value = mock_response

    with patch(
        "supertone_cli.client.get_client",
        return_value=mock_client,
    ):
        result = create_speech("Hello", "v1", "sona_speech_2", "ko")
        assert result == b"audio-bytes"


def test_create_speech_auth_error():
    from supertone_cli.client import create_speech

    mock_client = MagicMock()
    mock_client.text_to_speech.create_speech.side_effect = Exception("unauthorized")

    with patch(
        "supertone_cli.client.get_client",
        return_value=mock_client,
    ):
        with pytest.raises(AuthError):
            create_speech("Hello", "v1", "sona_speech_2", "ko")


def test_create_speech_api_error():
    from supertone_cli.client import create_speech

    mock_client = MagicMock()
    mock_client.text_to_speech.create_speech.side_effect = Exception("server error")

    with patch(
        "supertone_cli.client.get_client",
        return_value=mock_client,
    ):
        with pytest.raises(APIError):
            create_speech("Hello", "v1", "sona_speech_2", "ko")


def test_list_voices_returns_voice_list():
    from supertone_cli.client import list_voices
    from supertone_cli.models import Voice

    mock_client = MagicMock()
    mock_voice = MagicMock()
    mock_voice.voice_id = "v1"
    mock_voice.name = "Voice1"
    mock_voice.language = "ko"
    mock_voice.gender = "male"
    mock_voice.age = None
    mock_voice.use_cases = []

    mock_response = MagicMock()
    mock_response.items = [mock_voice]
    mock_client.voices.list_voices.return_value = mock_response

    with patch(
        "supertone_cli.client.get_client",
        return_value=mock_client,
    ):
        voices = list_voices()
        assert len(voices) == 1
        assert isinstance(voices[0], Voice)
        assert voices[0].id == "v1"


def test_predict_duration_returns_prediction():
    from supertone_cli.client import predict_duration
    from supertone_cli.models import Prediction

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.duration = 3.2
    mock_client.text_to_speech.predict_duration.return_value = mock_response

    with patch(
        "supertone_cli.client.get_client",
        return_value=mock_client,
    ):
        pred = predict_duration("Hello", "v1", "sona_speech_2", "ko")
        assert isinstance(pred, Prediction)
        assert pred.duration_seconds == 3.2


def test_clone_voice_returns_clone_result(tmp_path):
    from supertone_cli.client import clone_voice
    from supertone_cli.models import CloneResult

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.voice_id = "clone-1"
    mock_client.custom_voices.create_cloned_voice.return_value = mock_response

    sample = tmp_path / "sample.wav"
    sample.write_bytes(b"fake-audio")

    with patch(
        "supertone_cli.client.get_client",
        return_value=mock_client,
    ):
        result = clone_voice("my-voice", str(sample))
        assert isinstance(result, CloneResult)
        assert result.voice_id == "clone-1"


def test_get_usage_returns_usage():
    from supertone_cli.client import get_usage
    from supertone_cli.models import Usage

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.balance = 900
    mock_client.usage.get_credit_balance.return_value = mock_response

    with patch(
        "supertone_cli.client.get_client",
        return_value=mock_client,
    ):
        usage = get_usage()
        assert isinstance(usage, Usage)
        assert usage.remaining == 900


# ── Additional client wrapper coverage ──────────────────────────────


def test_search_voices_returns_filtered_list():
    from supertone_cli.client import search_voices
    from supertone_cli.models import Voice

    mock_client = MagicMock()
    mock_voice = MagicMock()
    mock_voice.voice_id = "v2"
    mock_voice.name = "Search Result"
    mock_voice.language = ["ko", "en"]
    mock_voice.gender = "female"
    mock_voice.age = "adult"
    mock_voice.use_cases = ["narration"]
    mock_response = MagicMock()
    mock_response.items = [mock_voice]
    mock_client.voices.search_voices.return_value = mock_response

    with patch("supertone_cli.client.get_client", return_value=mock_client):
        voices = search_voices(lang="ko", gender="female")
        assert len(voices) == 1
        assert isinstance(voices[0], Voice)
        assert voices[0].id == "v2"
        mock_client.voices.search_voices.assert_called_once_with(language="ko", gender="female")


def test_get_voice_returns_voice():
    from supertone_cli.client import get_voice
    from supertone_cli.models import Voice

    mock_client = MagicMock()
    mock_v = MagicMock()
    mock_v.voice_id = "v1"
    mock_v.name = "Test"
    mock_v.language = "ko"
    mock_v.gender = "male"
    mock_v.age = "adult"
    mock_v.use_cases = ["audiobook"]
    mock_client.voices.get_voice.return_value = mock_v

    with patch("supertone_cli.client.get_client", return_value=mock_client):
        voice = get_voice("v1")
        assert isinstance(voice, Voice)
        assert voice.id == "v1"
        assert voice.name == "Test"


def test_edit_custom_voice_returns_result():
    from supertone_cli.client import edit_custom_voice
    from supertone_cli.models import CloneResult

    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.voice_id = "v1"
    mock_resp.name = "Renamed"
    mock_client.custom_voices.edit_custom_voice.return_value = mock_resp

    with patch("supertone_cli.client.get_client", return_value=mock_client):
        result = edit_custom_voice("v1", name="Renamed")
        assert isinstance(result, CloneResult)
        assert result.voice_id == "v1"


def test_delete_custom_voice_calls_sdk():
    from supertone_cli.client import delete_custom_voice

    mock_client = MagicMock()
    with patch("supertone_cli.client.get_client", return_value=mock_client):
        delete_custom_voice("v1")
        mock_client.custom_voices.delete_custom_voice.assert_called_once_with(voice_id="v1")


def test_stream_speech_yields_chunks():
    from supertone_cli.client import stream_speech

    mock_client = MagicMock()
    mock_client.text_to_speech.stream_speech.return_value = [b"chunk1", b"chunk2"]

    with patch("supertone_cli.client.get_client", return_value=mock_client):
        chunks = list(stream_speech("Hello", "v1", "sona_speech_1", "ko"))
        assert chunks == [b"chunk1", b"chunk2"]


def test_get_usage_analytics_returns_list():
    from supertone_cli.client import get_usage_analytics

    mock_client = MagicMock()
    mock_bucket = MagicMock()
    mock_bucket.starting_at = "2026-04-01"
    mock_bucket.ending_at = "2026-04-02"
    mock_result = MagicMock()
    mock_result.minutes_used = 5.5
    mock_result.voice_id = "v1"
    mock_result.voice_name = "Voice1"
    mock_result.model = "sona_speech_2"
    mock_bucket.results = [mock_result]
    mock_response = MagicMock()
    mock_response.data = [mock_bucket]
    mock_client.usage.get_usage.return_value = mock_response

    with patch("supertone_cli.client.get_client", return_value=mock_client):
        results = get_usage_analytics("2026-04-01", "2026-04-02", "day")
        assert len(results) == 1
        assert results[0]["minutes_used"] == 5.5
        assert results[0]["voice_name"] == "Voice1"


def test_get_voice_usage_returns_list():
    from supertone_cli.client import get_voice_usage

    mock_client = MagicMock()
    mock_u = MagicMock()
    mock_u.date_ = "2026-04-01"
    mock_u.voice_id = "v1"
    mock_u.name = "Voice1"
    mock_u.total_minutes_used = 3.2
    mock_u.model = "sona_speech_2"
    mock_u.language = "ko"
    mock_response = MagicMock()
    mock_response.usages = [mock_u]
    mock_client.usage.get_voice_usage.return_value = mock_response

    with patch("supertone_cli.client.get_client", return_value=mock_client):
        results = get_voice_usage("2026-04-01", "2026-04-30")
        assert len(results) == 1
        assert results[0]["date"] == "2026-04-01"
        assert results[0]["minutes_used"] == 3.2


def test_list_custom_voices_via_sdk():
    """list_custom_voices uses the SDK directly (no httpx workaround)."""
    from supertone_cli.client import list_custom_voices
    from supertone_cli.models import Voice

    mock_client = MagicMock()
    mock_voice = MagicMock(spec=["voice_id", "name"])
    mock_voice.voice_id = "c1"
    mock_voice.name = "Custom1"
    mock_response = MagicMock()
    mock_response.items = [mock_voice]
    mock_client.custom_voices.list_custom_voices.return_value = mock_response

    with patch("supertone_cli.client.get_client", return_value=mock_client):
        voices = list_custom_voices()
        assert len(voices) == 1
        assert isinstance(voices[0], Voice)
        assert voices[0].id == "c1"
        assert voices[0].name == "Custom1"
        assert voices[0].type == "custom"
        mock_client.custom_voices.list_custom_voices.assert_called_once()


def test_create_speech_with_voice_settings():
    from supertone_cli.client import create_speech

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.result = b"audio-with-settings"
    mock_client.text_to_speech.create_speech.return_value = mock_response

    with patch("supertone_cli.client.get_client", return_value=mock_client):
        result = create_speech(
            "Hello",
            "v1",
            "sona_speech_2",
            "ko",
            style="calm",
            speed=1.2,
            pitch_shift=-1.0,
        )
        assert result == b"audio-with-settings"
        call_kwargs = mock_client.text_to_speech.create_speech.call_args.kwargs
        assert "style" in call_kwargs
        assert "voice_settings" in call_kwargs
