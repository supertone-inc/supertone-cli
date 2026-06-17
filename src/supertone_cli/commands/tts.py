"""TTS command: text-to-speech generation."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer

from supertone_cli.client import create_speech
from supertone_cli.config import get_default
from supertone_cli.errors import InputError
from supertone_cli.output import print_json

tts_app = typer.Typer(
    name="tts",
    help="Text-to-speech commands.",
)

VALID_MODELS = {
    "sona_speech_1",
    "supertonic_api_1",
    "supertonic_api_3",
    "sona_speech_2",
    "sona_speech_2_flash",
    "sona_speech_2t",
}

VALID_OUTPUT_FORMATS = {"wav", "mp3"}

# Model-parameter compatibility matrix
_FLASH_DISALLOWED = {"similarity", "text_guidance"}
_SUPERTONIC_ALLOWED = {"speed"}
_SUPERTONIC_MODELS = {"supertonic_api_1", "supertonic_api_3"}
_STREAM_MODELS = {"sona_speech_1"}


def validate_params(model: str, **kwargs: object) -> None:
    """Validate model-parameter compatibility."""
    if model not in VALID_MODELS:
        valid = ", ".join(sorted(VALID_MODELS))
        raise InputError(f"Unknown model: {model}. Valid models: {valid}")

    # Filter to only provided (non-None) params
    params = {k: v for k, v in kwargs.items() if v is not None}

    if model == "sona_speech_2_flash":
        bad = set(params) & _FLASH_DISALLOWED
        if bad:
            raise InputError(f"Not supported by {model}: {', '.join(sorted(bad))}")

    if model in _SUPERTONIC_MODELS:
        bad = set(params) - _SUPERTONIC_ALLOWED - {"stream"}
        if bad:
            raise InputError(
                f"Not supported by {model}: {', '.join(sorted(bad))}. "
                "Only speed is supported."
            )

    if params.get("stream") and model not in _STREAM_MODELS:
        raise InputError(f"Streaming requires sona_speech_1, but model is {model}.")


def _resolve_text(
    text: str | None,
    input_path: str | None,
) -> str:
    """Resolve input text from positional arg, file, or stdin."""
    sources = []
    if text:
        sources.append("positional")
    if input_path:
        sources.append("--input")

    stdin_has_data = not sys.stdin.isatty()

    if stdin_has_data and not sources:
        content = sys.stdin.read().strip()
        if not content:
            raise InputError("stdin is empty.")
        return content

    if len(sources) > 1:
        raise InputError("Ambiguous input: provide text OR --input, not both.")

    if not sources and not stdin_has_data:
        raise InputError(
            "No input provided. Pass text as argument, use --input <file>, "
            "or pipe via stdin."
        )

    if text:
        return text

    p = Path(input_path)  # type: ignore[arg-type]
    if not p.exists():
        raise InputError(f"File not found: {input_path}")
    content = p.read_text(encoding="utf-8").strip()
    if not content:
        raise InputError(f"File is empty: {input_path}")
    return content


def _is_batch_input(input_path: str | None) -> bool:
    """Check if input is a directory (batch mode)."""
    if not input_path:
        return False
    return Path(input_path).is_dir()


def _collect_batch_files(input_path: str) -> list[Path]:
    """Collect .txt files from a directory."""
    p = Path(input_path)
    files = sorted(p.glob("*.txt"))
    if not files:
        raise InputError(f"No .txt files found in: {input_path}")
    return files


def _build_settings_kwargs(
    speed: float | None,
    pitch: float | None,
    pitch_variance: float | None,
    similarity: float | None,
    text_guidance: float | None,
) -> dict:
    """Build voice_settings kwargs for client.create_speech."""
    settings: dict = {}
    if speed is not None:
        settings["speed"] = speed
    if pitch is not None:
        settings["pitch_shift"] = pitch
    if pitch_variance is not None:
        settings["pitch_variance"] = pitch_variance
    if similarity is not None:
        settings["similarity"] = similarity
    if text_guidance is not None:
        settings["text_guidance"] = text_guidance
    return settings


def _run_batch(
    input_path: str,
    outdir: str,
    output_format: str,
    voice: str,
    model: str,
    lang: str,
    style: str | None,
    fail_fast: bool,
    **voice_settings: object,
) -> None:
    """Process batch TTS for all .txt files in a directory."""
    files = _collect_batch_files(input_path)
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)

    succeeded = 0
    failed = 0

    for f in files:
        text = f.read_text(encoding="utf-8").strip()
        if not text:
            continue
        out_file = out / f"{f.stem}.{output_format}"
        try:
            audio = create_speech(
                text=text,
                voice=voice,
                model=model,
                lang=lang,
                output_format=output_format,
                style=style,
                **voice_settings,
            )
            out_file.write_bytes(audio)
            succeeded += 1
        except Exception as exc:
            failed += 1
            typer.echo(f"Error: {f.name}: {exc}", err=True)
            if fail_fast:
                raise InputError(f"Batch stopped: {f.name} failed") from exc

    typer.echo(
        f"{succeeded} succeeded, {failed} failed",
        err=True,
    )
    if failed:
        raise InputError(f"{failed} file(s) failed in batch")


def _run_stream(
    text: str,
    voice: str,
    model: str,
    lang: str,
    output: str | None,
    style: str | None = None,
    **voice_settings: object,
) -> None:
    """Stream TTS audio to the system audio device."""
    try:
        import sounddevice  # noqa: F401
    except (ImportError, TypeError):
        raise InputError(
            "sounddevice not installed. Install with: pip install supertone-cli[stream]"
        )

    from supertone_cli.client import stream_speech

    chunks: list[bytes] = []
    for chunk in stream_speech(
        text=text,
        voice=voice,
        model=model,
        lang=lang,
        style=style,
        **voice_settings,
    ):
        chunks.append(chunk)

    if output and output != "-":
        Path(output).write_bytes(b"".join(chunks))

    total_bytes = sum(len(c) for c in chunks)
    typer.echo(f"Streamed: {total_bytes} bytes", err=True)


def _run_tts(  # noqa: PLR0913
    text: str | None,
    input: str | None,
    output: str | None,
    output_format: str,
    voice: str | None,
    model: str | None,
    lang: str | None,
    style: str | None,
    format: str,
    outdir: str | None = None,
    fail_fast: bool = False,
    stream: bool = False,
    speed: float | None = None,
    pitch: float | None = None,
    pitch_variance: float | None = None,
    similarity: float | None = None,
    text_guidance: float | None = None,
) -> None:
    """Core TTS logic shared by the command."""
    if output_format not in VALID_OUTPUT_FORMATS:
        valid = ", ".join(sorted(VALID_OUTPUT_FORMATS))
        raise InputError(f"Unsupported format: {output_format}. Valid: {valid}")

    resolved_voice = voice or get_default("default_voice")
    if not resolved_voice:
        raise InputError(
            "No voice specified. Use --voice <id> or "
            "set a default: supertone config set default_voice <id>"
        )

    # Streaming only supports sona_speech_1. When the user hasn't explicitly
    # passed -m/--model, default the streaming path to sona_speech_1 so it works
    # without an extra flag (config default_model is bypassed here for the same
    # reason — any other default would always fail streaming).
    if stream and model is None:
        resolved_model = "sona_speech_1"
    else:
        resolved_model = model or get_default("default_model") or "sona_speech_2"
    resolved_lang = lang or get_default("default_lang") or "ko"

    # Validate model-parameter compatibility
    validate_params(
        resolved_model,
        speed=speed,
        pitch_shift=pitch,
        pitch_variance=pitch_variance,
        similarity=similarity,
        text_guidance=text_guidance,
        stream=stream if stream else None,
    )

    voice_settings = _build_settings_kwargs(
        speed, pitch, pitch_variance, similarity, text_guidance
    )

    # Batch mode: directory input + outdir
    if _is_batch_input(input) and outdir:
        _run_batch(
            input,  # type: ignore[arg-type]
            outdir,
            output_format,
            resolved_voice,
            resolved_model,
            resolved_lang,
            style,
            fail_fast,
            **voice_settings,
        )
        return

    if format == "json" and output == "-":
        raise InputError(
            "Cannot use --format json with --output -: both write to stdout."
        )

    resolved_text = _resolve_text(text, input)

    # Streaming mode
    if stream:
        _run_stream(
            resolved_text,
            resolved_voice,
            resolved_model,
            resolved_lang,
            output,
            style=style,
            **voice_settings,
        )
        return

    if output == "-":
        out_path = None
    elif output:
        out_path = Path(output)
    else:
        out_path = Path(f"output.{output_format}")

    audio_bytes = create_speech(
        text=resolved_text,
        voice=resolved_voice,
        model=resolved_model,
        lang=resolved_lang,
        output_format=output_format,
        style=style,
        **voice_settings,
    )

    if out_path is None:
        sys.stdout.buffer.write(audio_bytes)
    else:
        out_path.write_bytes(audio_bytes)

    if format == "json":
        print_json(
            {
                "output_file": str(out_path) if out_path else "-",
                "voice_id": resolved_voice,
                "model": resolved_model,
                "lang": resolved_lang,
                "output_format": output_format,
            }
        )


def register_tts_command(app: typer.Typer) -> None:
    """Register TTS command directly on the main app."""

    @app.command("tts")
    def tts_cmd(  # noqa: PLR0913
        text: Optional[str] = typer.Argument(None, help="Text to synthesize."),
        input: Optional[str] = typer.Option(
            None, "--input", "-i", help="Path to text file."
        ),
        output: Optional[str] = typer.Option(
            None,
            "--output",
            "-o",
            help="Output file path. Use '-' for stdout.",
        ),
        output_format: str = typer.Option(
            "wav",
            "--output-format",
            help="Audio format: wav, mp3.",
        ),
        voice: Optional[str] = typer.Option(None, "--voice", "-v", help="Voice ID."),
        model: Optional[str] = typer.Option(None, "--model", "-m", help="TTS model."),
        lang: Optional[str] = typer.Option(None, "--lang", "-l", help="Language code."),
        style: Optional[str] = typer.Option(None, "--style", "-s", help="Voice style."),
        format: str = typer.Option(
            "text",
            "--format",
            "-f",
            help="Output format: text or json.",
        ),
        outdir: Optional[str] = typer.Option(
            None,
            "--outdir",
            help="Output directory for batch mode.",
        ),
        fail_fast: bool = typer.Option(
            False,
            "--fail-fast",
            help="Stop batch on first error.",
        ),
        stream: bool = typer.Option(
            False,
            "--stream",
            help="Stream audio to system output.",
        ),
        speed: Optional[float] = typer.Option(None, "--speed", help="Speaking speed."),
        pitch: Optional[float] = typer.Option(None, "--pitch", help="Pitch shift."),
        pitch_variance: Optional[float] = typer.Option(
            None, "--pitch-variance", help="Pitch variance."
        ),
        similarity: Optional[float] = typer.Option(
            None, "--similarity", help="Voice similarity."
        ),
        text_guidance: Optional[float] = typer.Option(
            None, "--text-guidance", help="Text guidance."
        ),
    ) -> None:
        """Generate speech from text."""
        _run_tts(
            text,
            input,
            output,
            output_format,
            voice,
            model,
            lang,
            style,
            format,
            outdir=outdir,
            fail_fast=fail_fast,
            stream=stream,
            speed=speed,
            pitch=pitch,
            pitch_variance=pitch_variance,
            similarity=similarity,
            text_guidance=text_guidance,
        )


def register_predict_command(app: typer.Typer) -> None:
    """Register TTS predict command on the main app."""
    from dataclasses import asdict

    @app.command("tts-predict")
    def predict_cmd(
        text: Optional[str] = typer.Argument(
            None, help="Text to predict duration for."
        ),
        input: Optional[str] = typer.Option(
            None, "--input", "-i", help="Path to text file."
        ),
        voice: Optional[str] = typer.Option(None, "--voice", "-v", help="Voice ID."),
        model: Optional[str] = typer.Option(None, "--model", "-m", help="TTS model."),
        lang: Optional[str] = typer.Option(None, "--lang", "-l", help="Language code."),
        format: str = typer.Option(
            "text",
            "--format",
            "-f",
            help="Output format: text or json.",
        ),
    ) -> None:
        """Predict audio duration without generating."""
        import supertone_cli.client as _client

        resolved_voice = voice or get_default("default_voice")
        if not resolved_voice:
            raise InputError(
                "No voice specified. Use --voice <id> or "
                "set a default: "
                "supertone config set default_voice <id>"
            )

        resolved_model = model or get_default("default_model") or "sona_speech_2"
        resolved_lang = lang or get_default("default_lang") or "ko"

        resolved_text = _resolve_text(text, input)

        prediction = _client.predict_duration(
            resolved_text,
            resolved_voice,
            resolved_model,
            resolved_lang,
        )

        if format == "json":
            print_json(asdict(prediction))
            return

        typer.echo(
            f"Duration: {prediction.duration_seconds}s | "
            f"Estimated credits: {prediction.estimated_credits}"
        )
