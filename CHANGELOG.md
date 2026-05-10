# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-05-10

### Changed

- Bump `supertone` minimum to `>=0.2.1` and revert `list_custom_voices` from the raw httpx workaround back to the SDK call now that the upstream Pydantic model makes `description` optional (resolves ISSUE-024 via ISSUE-028 / PR #52).
- `voices list-custom --format json` may now include `languages`, `gender`, `age`, and `use_cases` fields when the SDK returns them (previously omitted).

### Fixed

- Repository URLs in `pyproject.toml` corrected to point at `supertone-inc/supertone-cli`.
- Test stability on Windows CI for `voices clone` and config file permissions.
- Test import block ordering (blank line between third-party and first-party imports).

## [0.1.0] - 2026-04-14

### Added

- `supertone tts` — text-to-speech generation from inline text, file (`--input`), or stdin
- `supertone tts` batch mode — process a directory of `.txt` files via `--input <dir> --outdir <dir>`
- `supertone tts --stream` — real-time streaming playback via sounddevice (requires `[stream]` extra)
- `supertone tts-predict` — estimate audio duration without generating speech
- Voice setting flags: `--speed`, `--pitch`, `--pitch-variance`, `--similarity`, `--text-guidance`, `--style`
- Model support: `sona_speech_1`, `sona_speech_2`, `sona_speech_2_flash`, `sona_speech_2t`, `supertonic_api_1` with per-model parameter validation
- Output format selection: `--output-format wav` or `mp3`
- `supertone voices list` — display preset and custom voices (`--type preset|custom`)
- `supertone voices search` — filter by language, gender, age, use case, or keyword
- `supertone voices get` — inspect a specific voice's details
- `supertone voices clone` — create a custom voice from an audio sample
- `supertone voices edit` — rename or update description of a custom voice
- `supertone voices delete` — delete a custom voice (with `--yes` to skip confirmation)
- `supertone usage balance` — display API credit balance
- `supertone usage analytics` — per-period usage breakdown (`--start`, `--end`, `--bucket`)
- `supertone usage voices` — per-voice usage breakdown
- `supertone config init|set|get|list` — manage API key and defaults via `~/.config/supertone/config.toml`
- `--format json` flag on all read commands for machine-readable output to stdout
- Human-readable output (tables, errors) to stderr; audio/JSON to stdout for safe piping
- `NO_COLOR` environment variable support
- Exit codes: 0 (success), 1 (API error), 2 (auth error), 3 (input error), 130 (interrupted)
- API key sanitization in error messages
- Config file permissions set to `0600`
- Lazy imports for fast CLI startup
- CI pipeline with GitHub Actions (lint + test + coverage gate ≥ 80%, Python 3.12/3.13, ubuntu/macOS)
- MIT license

[0.1.1]: https://github.com/supertone-inc/supertone-cli/releases/tag/v0.1.1
[0.1.0]: https://github.com/supertone-inc/supertone-cli/releases/tag/v0.1.0
