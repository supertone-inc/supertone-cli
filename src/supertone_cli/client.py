"""SDK client wrapper — the ONLY module that imports supertone.

All SDK calls go through this module. SDK exceptions are translated
into CLI-friendly errors (AuthError, APIError).

SDK: supertone.Supertone(api_key=...)
  .text_to_speech: create_speech, stream_speech, predict_duration
  .voices: list_voices, search_voices
  .custom_voices: create_cloned_voice
  .usage: get_credit_balance
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator

from supertone_cli.config import get_api_key
from supertone_cli.errors import APIError, AuthError
from supertone_cli.models import (
    CloneResult,
    Prediction,
    Usage,
    Voice,
)

_client: Any = None

_SENTINEL = object()


def _attr(obj: Any, name: str, default: Any = None) -> Any:
    """Safe attribute access on SDK response objects.

    Equivalent to ``obj.name if hasattr(obj, "name") else default``,
    but in a single call.  For falsy-aware defaults (e.g. empty list
    when the attribute is None), pass the desired default explicitly.
    """
    return getattr(obj, name, default)


def _languages(obj: Any) -> list[str]:
    """Extract the language field from an SDK voice object.

    The SDK may return a single string or a list.  This helper
    normalises both forms to ``list[str]``.
    """
    lang = getattr(obj, "language", None)
    if isinstance(lang, list):
        return lang
    if lang:
        return [lang]
    return []


def _build_voice(v: Any, voice_type: str = "preset") -> Voice:
    """Convert an SDK voice response object to a CLI Voice model."""
    return Voice(
        id=_attr(v, "voice_id", str(v)),
        name=_attr(v, "name", ""),
        type=voice_type,
        languages=_languages(v),
        gender=_attr(v, "gender"),
        age=_attr(v, "age"),
        use_cases=_attr(v, "use_cases") or [],
    )


def _is_auth_error(exc: Exception) -> bool:
    """Detect authentication errors from SDK exceptions.

    Priority order:
    1. Typed SDK exceptions (UnauthorizedErrorResponse, ForbiddenErrorResponse)
    2. status_code attribute on SupertoneError base (401, 403)
    3. String heuristic fallback for non-SDK exceptions (e.g. plain Exception)
       -- only used when the exception has NO status_code attribute at all.
    """
    # 1. Typed SDK exception classes (most reliable)
    try:
        from supertone.errors import (
            ForbiddenErrorResponse,
            UnauthorizedErrorResponse,
        )

        if isinstance(exc, (UnauthorizedErrorResponse, ForbiddenErrorResponse)):
            return True
    except ImportError:
        pass

    # 2. Check status_code attribute on SupertoneError base
    status = getattr(exc, "status_code", None)
    if status is not None:
        # SDK exception with a known status code -- trust the code, not the message
        return status in (401, 403)

    # 3. Last-resort string heuristic fallback for non-SDK exceptions
    # (e.g., plain Exception from unexpected code paths)
    msg = str(exc).lower()
    return any(kw in msg for kw in ("unauthorized", "forbidden", "invalid key", "401"))


def get_client() -> Any:
    """Return the SDK client singleton (lazy-initialized)."""
    global _client  # noqa: PLW0603
    if _client is not None:
        return _client

    key = get_api_key()
    if not key:
        raise AuthError(
            "API key not configured. Run: supertone config set api_key <key>"
        )

    # Lazy import -- SDK loaded only when needed (startup perf).
    from supertone import Supertone

    _client = Supertone(api_key=key)
    return _client


def _get_language_enum(lang: str) -> Any:
    """Convert language string to SDK enum."""
    from supertone.models import (
        APIConvertTextToSpeechUsingCharacterRequestLanguage as LangEnum,
    )

    mapping = {member.value: member for member in LangEnum}
    if lang not in mapping:
        from supertone_cli.errors import InputError

        raise InputError(
            f"Unsupported language: {lang}. Valid: {', '.join(sorted(mapping.keys()))}"
        )
    return mapping[lang]


def _get_model_enum(model: str) -> Any:
    """Convert model string to SDK enum."""
    from supertone.models import (
        APIConvertTextToSpeechUsingCharacterRequestModel as ModelEnum,
    )

    mapping = {member.value: member for member in ModelEnum}
    if model not in mapping:
        from supertone_cli.errors import InputError

        raise InputError(
            f"Unsupported model: {model}. Valid: {', '.join(sorted(mapping.keys()))}"
        )
    return mapping[model]


def _get_format_enum(fmt: str) -> Any:
    """Convert output format string to SDK enum."""
    from supertone.models import (
        APIConvertTextToSpeechUsingCharacterRequestOutputFormat as FmtEnum,
    )

    mapping = {member.value: member for member in FmtEnum}
    if fmt not in mapping:
        from supertone_cli.errors import InputError

        raise InputError(
            f"Unsupported format: {fmt}. Valid: {', '.join(sorted(mapping.keys()))}"
        )
    return mapping[fmt]


def _build_voice_settings(**params: Any) -> Any | None:
    """Build SDK VoiceSettings from CLI params. Returns None if no settings."""
    settings = {
        k: v
        for k, v in params.items()
        if v is not None
        and k
        in (
            "pitch_shift",
            "pitch_variance",
            "speed",
            "similarity",
            "text_guidance",
        )
    }
    if not settings:
        return None
    from supertone.models import ConvertTextToSpeechParameters

    return ConvertTextToSpeechParameters(**settings)


# -- SDK operation wrappers ---------------------------------------------------


def create_speech(
    text: str,
    voice: str,
    model: str,
    lang: str,
    output_format: str = "wav",
    style: str | None = None,
    include_phonemes: bool = False,
    **params: Any,
) -> bytes:
    """Generate speech audio bytes."""
    client = get_client()
    try:
        voice_settings = _build_voice_settings(**params)
        kwargs: dict[str, Any] = {
            "voice_id": voice,
            "text": text,
            "language": _get_language_enum(lang),
            "model": _get_model_enum(model),
            "output_format": _get_format_enum(output_format),
        }
        if style is not None:
            kwargs["style"] = style
        if voice_settings is not None:
            kwargs["voice_settings"] = voice_settings
        if include_phonemes:
            kwargs["include_phonemes"] = True

        response = client.text_to_speech.create_speech(**kwargs)
        # response.result is an httpx.Response (streaming)
        result = _attr(response, "result", _SENTINEL)
        if result is not _SENTINEL:
            read_fn = _attr(result, "read")
            if read_fn:
                read_fn()
            content = _attr(result, "content", _SENTINEL)
            if content is not _SENTINEL:
                return content
            return result
        return response
    except (AuthError, APIError):
        raise
    except Exception as exc:
        if _is_auth_error(exc):
            raise AuthError(str(exc)) from exc
        raise APIError(str(exc)) from exc


def stream_speech(
    text: str,
    voice: str,
    model: str,
    lang: str,
    output_format: str = "wav",
    style: str | None = None,
    **params: Any,
) -> Iterator[bytes]:
    """Stream speech audio chunks."""
    client = get_client()
    try:
        voice_settings = _build_voice_settings(**params)
        kwargs: dict[str, Any] = {
            "voice_id": voice,
            "text": text,
            "language": _get_language_enum(lang),
            "model": _get_model_enum(model),
            "output_format": _get_format_enum(output_format),
        }
        if style is not None:
            kwargs["style"] = style
        if voice_settings is not None:
            kwargs["voice_settings"] = voice_settings

        response = client.text_to_speech.stream_speech(**kwargs)
        if hasattr(response, "__iter__"):
            yield from response
        else:
            yield response
    except (AuthError, APIError):
        raise
    except Exception as exc:
        if _is_auth_error(exc):
            raise AuthError(str(exc)) from exc
        raise APIError(str(exc)) from exc


def predict_duration(
    text: str,
    voice: str,
    model: str,
    lang: str,
) -> Prediction:
    """Predict audio duration without generating."""
    client = get_client()
    try:
        response = client.text_to_speech.predict_duration(
            voice_id=voice,
            text=text,
            language=_get_language_enum(lang),
            model=_get_model_enum(model),
        )
        duration = _attr(response, "duration", 0.0)
        return Prediction(
            duration_seconds=float(duration),
            estimated_credits=0,  # SDK doesn't return credit estimate directly
        )
    except (AuthError, APIError):
        raise
    except Exception as exc:
        if _is_auth_error(exc):
            raise AuthError(str(exc)) from exc
        raise APIError(str(exc)) from exc


def list_voices() -> list[Voice]:
    """List all available voices."""
    client = get_client()
    try:
        response = client.voices.list_voices()
        items = _attr(response, "items", [])
        return [_build_voice(v) for v in items]
    except (AuthError, APIError):
        raise
    except Exception as exc:
        if _is_auth_error(exc):
            raise AuthError(str(exc)) from exc
        raise APIError(str(exc)) from exc


def list_custom_voices() -> list[Voice]:
    """List custom (cloned) voices."""
    client = get_client()
    try:
        response = client.custom_voices.list_custom_voices()
        items = _attr(response, "items", [])
        return [_build_voice(v, voice_type="custom") for v in items]
    except (AuthError, APIError):
        raise
    except Exception as exc:
        if _is_auth_error(exc):
            raise AuthError(str(exc)) from exc
        raise APIError(str(exc)) from exc


def search_voices(**filters: Any) -> list[Voice]:
    """Search voices with filters."""
    client = get_client()
    try:
        # Map CLI filter names to SDK parameter names
        sdk_params: dict[str, Any] = {}
        if filters.get("lang"):
            sdk_params["language"] = filters["lang"]
        if filters.get("gender"):
            sdk_params["gender"] = filters["gender"]
        if filters.get("age"):
            sdk_params["age"] = filters["age"]
        if filters.get("use_case"):
            sdk_params["use_case"] = filters["use_case"]
        if filters.get("query"):
            sdk_params["name"] = filters["query"]

        response = client.voices.search_voices(**sdk_params)
        items = _attr(response, "items", [])
        return [_build_voice(v) for v in items]
    except (AuthError, APIError):
        raise
    except Exception as exc:
        if _is_auth_error(exc):
            raise AuthError(str(exc)) from exc
        raise APIError(str(exc)) from exc


def clone_voice(name: str, sample_path: str) -> CloneResult:
    """Clone a voice from an audio sample."""
    client = get_client()
    try:
        file_path = Path(sample_path)
        file_content = file_path.read_bytes()
        file_name = file_path.name

        from supertone.models.create_cloned_voiceop import Files

        files = Files(file_name=file_name, content=file_content)

        response = client.custom_voices.create_cloned_voice(
            files=files,
            name=name,
        )
        voice_id = _attr(response, "voice_id", "")
        return CloneResult(voice_id=voice_id, name=name)
    except (AuthError, APIError):
        raise
    except Exception as exc:
        if _is_auth_error(exc):
            raise AuthError(str(exc)) from exc
        raise APIError(str(exc)) from exc


def get_voice(voice_id: str) -> Voice:
    """Get details of a specific voice."""
    client = get_client()
    try:
        v = client.voices.get_voice(voice_id=voice_id)
        return Voice(
            id=_attr(v, "voice_id", voice_id),
            name=_attr(v, "name", ""),
            type="preset",
            languages=_languages(v),
            gender=_attr(v, "gender"),
            age=_attr(v, "age"),
            use_cases=_attr(v, "use_cases") or [],
        )
    except (AuthError, APIError):
        raise
    except Exception as exc:
        if _is_auth_error(exc):
            raise AuthError(str(exc)) from exc
        raise APIError(str(exc)) from exc


def edit_custom_voice(
    voice_id: str,
    name: str | None = None,
    description: str | None = None,
) -> CloneResult:
    """Edit a custom voice's name or description."""
    client = get_client()
    try:
        kwargs: dict[str, Any] = {"voice_id": voice_id}
        if name is not None:
            kwargs["name"] = name
        if description is not None:
            kwargs["description"] = description
        response = client.custom_voices.edit_custom_voice(**kwargs)
        return CloneResult(
            voice_id=_attr(response, "voice_id", voice_id),
            name=_attr(response, "name", name or ""),
        )
    except (AuthError, APIError):
        raise
    except Exception as exc:
        if _is_auth_error(exc):
            raise AuthError(str(exc)) from exc
        raise APIError(str(exc)) from exc


def delete_custom_voice(voice_id: str) -> None:
    """Delete a custom voice."""
    client = get_client()
    try:
        client.custom_voices.delete_custom_voice(voice_id=voice_id)
    except (AuthError, APIError):
        raise
    except Exception as exc:
        if _is_auth_error(exc):
            raise AuthError(str(exc)) from exc
        raise APIError(str(exc)) from exc


def get_usage() -> Usage:
    """Get API credit balance."""
    client = get_client()
    try:
        response = client.usage.get_credit_balance()
        balance = _attr(response, "balance", 0)
        return Usage(
            plan="",
            used=0,
            remaining=int(balance) if balance else 0,
        )
    except (AuthError, APIError):
        raise
    except Exception as exc:
        if _is_auth_error(exc):
            raise AuthError(str(exc)) from exc
        raise APIError(str(exc)) from exc


def get_usage_analytics(
    start_time: str,
    end_time: str,
    bucket_width: str = "day",
) -> list[dict]:
    """Get usage analytics for a date range."""
    client = get_client()
    try:
        from supertone.models.get_usageop import BucketWidth

        bw = BucketWidth(bucket_width)
        response = client.usage.get_usage(
            start_time=start_time,
            end_time=end_time,
            bucket_width=bw,
        )
        results = []
        data = _attr(response, "data", [])
        for bucket in data:
            for r in _attr(bucket, "results", []):
                results.append(
                    {
                        "period_start": _attr(bucket, "starting_at", ""),
                        "period_end": _attr(bucket, "ending_at", ""),
                        "minutes_used": _attr(r, "minutes_used", 0),
                        "voice_id": _attr(r, "voice_id"),
                        "voice_name": _attr(r, "voice_name"),
                        "model": _attr(r, "model"),
                    }
                )
        return results
    except (AuthError, APIError):
        raise
    except Exception as exc:
        if _is_auth_error(exc):
            raise AuthError(str(exc)) from exc
        raise APIError(str(exc)) from exc


def get_voice_usage(start_date: str, end_date: str) -> list[dict]:
    """Get per-voice usage for a date range."""
    client = get_client()
    try:
        response = client.usage.get_voice_usage(
            start_date=start_date,
            end_date=end_date,
        )
        usages = _attr(response, "usages", [])
        return [
            {
                "date": _attr(u, "date_", ""),
                "voice_id": _attr(u, "voice_id", ""),
                "name": _attr(u, "name"),
                "minutes_used": _attr(u, "total_minutes_used", 0),
                "model": _attr(u, "model"),
                "language": _attr(u, "language"),
            }
            for u in usages
        ]
    except (AuthError, APIError):
        raise
    except Exception as exc:
        if _is_auth_error(exc):
            raise AuthError(str(exc)) from exc
        raise APIError(str(exc)) from exc
