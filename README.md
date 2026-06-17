# supertone-cli

[![CI](https://github.com/supertone-inc/supertone-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/supertone-inc/supertone-cli/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/supertone-cli.svg)](https://pypi.org/project/supertone-cli/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Command-line interface for the [Supertone](https://supertone.ai/) Text-to-Speech API. Generate, stream, batch, and manage voices directly from the terminal.

## Features

- **Synthesize speech** from a string, file, or stdin; write to a file or stdout.
- **Stream audio** to your system output in real time (`--stream`).
- **Batch process** an entire directory of `.txt` files.
- **Predict duration** of a synthesis request before spending credits.
- **Manage voices**: list, search, inspect, clone, edit, and delete custom voices.
- **Usage insights**: credit balance, per-period analytics, per-voice breakdown.
- **Pipe friendly**: human-readable output to stderr, machine-readable JSON to stdout.

## Installation

```bash
pip install supertone-cli
```

Requires Python 3.12 or newer.

For real-time audio streaming, install the optional extra (adds `sounddevice` and a PortAudio dependency):

```bash
pip install "supertone-cli[stream]"
```

## Authentication

Get an API key from the Supertone dashboard, then set it one of two ways.

**Option 1 — environment variable** (preferred for CI and scripts):

```bash
export SUPERTONE_API_KEY="sk-..."
```

**Option 2 — config file** (persisted at `~/.config/supertone/config.toml` with `0600` permissions):

```bash
supertone config set api_key sk-...
```

Resolution order: **CLI flags > environment variables > config file > built-in defaults**.

You can also set defaults so you don't need to pass `--voice`, `--model`, or `--lang` every time:

```bash
supertone config set default_voice <voice-id>
supertone config set default_model sona_speech_2
supertone config set default_lang ko
```

Or run the interactive setup:

```bash
supertone config init
```

## Quickstart

```bash
# Synthesize a short line to output.wav in the current directory
supertone tts "안녕하세요, 수퍼톤입니다." --voice <voice-id>

# Pick a voice
supertone voices search --lang ko --gender female
supertone voices get <voice-id>

# Check your credit balance
supertone usage balance
```

## Examples

### TTS

```bash
# Inline text → file
supertone tts "Hello, world." -v <voice-id> -o hello.wav

# From a file
supertone tts -i script.txt -v <voice-id> -o narration.wav

# From stdin, pipe audio to stdout, then into ffplay
echo "Streaming straight to the speakers" \
  | supertone tts -v <voice-id> -o - \
  | ffplay -autoexit -nodisp -

# MP3 output with voice parameters
supertone tts "Slow and steady." \
  -v <voice-id> --output-format mp3 \
  --speed 0.9 --pitch -2

# Real-time streaming playback (requires [stream] extra)
supertone tts "Low-latency speech." -v <voice-id> --stream

# Batch: one .txt file → one audio file per entry
supertone tts -i scripts/ --outdir audio/ -v <voice-id>
```

### Voices

```bash
supertone voices list                         # all voices
supertone voices list --type custom           # your custom voices only
supertone voices search --lang en --age adult
supertone voices get <voice-id>
supertone voices clone --name "My Voice" --sample sample.wav
supertone voices edit <voice-id> --name "Renamed"
supertone voices delete <voice-id> --yes
```

### Predict & usage

```bash
# Estimate duration without spending credits
supertone tts-predict "How long will this take?" -v <voice-id>

supertone usage balance
supertone usage analytics --start 2026-04-01 --end 2026-04-30
supertone usage voices    --start 2026-04-01 --end 2026-04-30
```

### JSON output

Every read command supports `--format json` for scripting:

```bash
supertone voices list --format json | jq '.[] | select(.type=="custom")'
supertone usage balance --format json
```

Human-readable output (tables, progress, errors) goes to **stderr**. Machine-readable JSON or audio bytes go to **stdout**. This means you can safely pipe stdout without polluting it.

## Configuration keys

| Key | Description |
|-----|-------------|
| `api_key` | Supertone API key (also via `SUPERTONE_API_KEY`) |
| `default_voice` | Voice ID used when `--voice` is omitted |
| `default_model` | Model used when `--model` is omitted (default `sona_speech_2`) |
| `default_lang` | Language used when `--lang` is omitted (default `ko`) |

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | General / API error |
| `2` | Authentication error (missing or invalid API key) |
| `3` | Input validation error |
| `130` | Interrupted (Ctrl-C) |

## Supported models

`sona_speech_1`, `sona_speech_2`, `sona_speech_2_flash`, `sona_speech_2t`, `supertonic_api_1`, `supertonic_api_3`. Parameter compatibility varies by model; the CLI validates this and returns exit code `3` on mismatches.

`supertonic_api_3` supports 31 languages and accepts only `--speed` for voice settings (other voice settings are rejected with exit code `3`).

Streaming (`--stream`) requires `sona_speech_1`. When no `--model` is given, the CLI selects it automatically, so `--stream` works without an explicit `-m sona_speech_1`.

## Development

```bash
git clone https://github.com/supertone-inc/supertone-cli.git
cd supertone-cli
uv sync --extra dev
uv run pytest -q
uv run supertone --help
```

## License

MIT — see [LICENSE](LICENSE).
