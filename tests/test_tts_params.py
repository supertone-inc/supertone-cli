"""Tests for ISSUE-006: TTS parameter validation."""

import pytest

from supertone_cli.commands.tts import validate_params
from supertone_cli.errors import InputError


def test_flash_rejects_similarity():
    with pytest.raises(InputError):
        validate_params("sona_speech_2_flash", similarity=0.8)


def test_flash_rejects_text_guidance():
    with pytest.raises(InputError):
        validate_params("sona_speech_2_flash", text_guidance=0.5)


def test_sona1_allows_stream():
    validate_params("sona_speech_1", stream=True)


def test_sona2_rejects_stream():
    with pytest.raises(InputError):
        validate_params("sona_speech_2", stream=True)


def test_supertonic_rejects_pitch():
    with pytest.raises(InputError):
        validate_params("supertonic_api_1", pitch=0.5)


def test_supertonic_api_3_rejects_pitch():
    with pytest.raises(InputError):
        validate_params("supertonic_api_3", pitch=0.5)


def test_supertonic_api_3_allows_speed_only():
    validate_params("supertonic_api_3", speed=1.1)


def test_sona2_allows_speed_and_pitch():
    validate_params("sona_speech_2", speed=1.2, pitch=0.5)


def test_invalid_model_raises():
    with pytest.raises(InputError, match="invalid_model"):
        validate_params("invalid_model")


def test_valid_model_no_params():
    validate_params("sona_speech_2")
    validate_params("sona_speech_1")
    validate_params("sona_speech_2_flash")
    validate_params("supertonic_api_1")
    validate_params("sona_speech_2t")


def test_sona2t_allows_full_params():
    """sona_speech_2t is a full-featured model — all voice settings allowed."""
    validate_params(
        "sona_speech_2t",
        speed=1.0,
        pitch_shift=0.5,
        pitch_variance=0.8,
        similarity=0.9,
        text_guidance=0.7,
    )
