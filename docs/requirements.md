# Requirements — Supertone CLI (Phase 1)

**Version**: 1.0
**Date**: 2026-04-03
**Source PRD**: PRD.md v1.1
**Confidence**: Medium (see Assumptions and Risks for uncertain areas)

---

## Goals (from PRD)

1. **Code-free TTS** — Generate speech from the terminal without writing Python code.
2. **Pipeline integration** — Support stdin/stdout, batch processing, and JSON output for composability with existing Unix tools.
3. **Fast onboarding** — Working from `pip install` to first TTS output in under 3 minutes.
4. **Full SDK surface exposure** — TTS, voice management, voice cloning, and usage monitoring accessible from the CLI.

---

## Primary User

**Content Creator** — Produces YouTube narration, short-form voiceover, audiobooks, or game assets. Comfortable with a terminal but may not write Python code. Wants to automate repetitive TTS tasks.

**Secondary User** — Automation pipeline builder. Developer who calls TTS from shell scripts or CI systems, composing LLM → translate → TTS → edit workflows.

---

## User Stories (prioritized — Must -> Should -> Could)

### Must

**US-1** — As a content creator, I want to type a line of text and receive an audio file so that I do not need to write a Python script every time.
- Acceptance Criteria:
  - Given a valid API key and voice ID, when I run `supertone tts "Hello"`, then an audio file named `output.wav` is created in the current directory.
  - Given `--output hello.wav`, then the file is written to the specified path.
  - Given the command succeeds, then exit code is 0.
  - Given the API returns an error, then exit code is 1 (general) or 2 (authentication) and a human-readable message with a suggested fix is printed to stderr.

**US-2** — As a content creator, I want to pass a text file as input so that I can process long scripts.
- Acceptance Criteria:
  - Given `--input script.txt`, when the file exists and is non-empty, then the full file contents are sent to the TTS API.
  - Given `--input script.txt` and the file does not exist, then exit code is 3 and an error message is printed to stderr.
  - Given `--input script.txt` and the file is empty, then exit code is 3 and an error message states the file is empty.

**US-3** — As a content creator, I want to select voice, model, language, style, and output format so that I can match the voice to my content.
- Acceptance Criteria:
  - Given `--voice <id>`, the specified voice ID is sent to the API.
  - Given no `--voice` and a `default_voice` is set in config, the config value is used.
  - Given no `--voice` and no config default, exit code is 3 and an error message instructs the user to specify `--voice` or run `supertone config set default_voice`.
  - Given `--model sona_speech_2`, the model parameter sent to the API is `sona_speech_2`.
  - Given `--model` is omitted, the default model `sona_speech_2` is used.
  - Given `--lang ko`, the language code `ko` is sent to the API.
  - Given `--output-format mp3`, the API is called with the mp3 format parameter and the output file has a `.mp3` extension.
  - Given `--style <style_id>`, the style parameter is sent to the API.

**US-5** — As a pipeline builder, I want to pipe text into the TTS command so that I can chain tools.
- Acceptance Criteria:
  - Given `echo "text" | supertone tts`, when stdin is not a TTY, the piped text is used as input.
  - Given both stdin and positional text argument are provided, exit code is 3 and an error message reports ambiguous input.
  - Given stdin is a TTY and no text argument or `--input` flag is given, exit code is 3 and an error message instructs the user on valid input methods.

**US-6** — As a pipeline builder, I want to output audio to stdout so that I can pipe it to other tools.
- Acceptance Criteria:
  - Given `supertone tts "text" --output -`, audio bytes are written to stdout and no other output is written to stdout.
  - Given stdout is not a TTY (i.e., redirected), progress indicators and color formatting are disabled automatically.
  - Given stdout is not a TTY, all human-readable output (table headers, progress bars) is written to stderr only.

**US-7** — As a content creator, I want to convert multiple text files at once so that I can process large volumes of content.
- Acceptance Criteria:
  - Given `--input ./scripts/ --outdir ./audio/`, all `.txt` files in `./scripts/` are processed.
  - Given `--input "scripts/*.txt" --outdir ./audio/`, all files matching the glob pattern are processed.
  - Given a file `script1.txt` in the input, the output file is `script1.wav` (or the extension matching `--output-format`) placed in `--outdir`.
  - Given one file fails during batch processing, the remaining files continue to be processed and a summary of failures is printed to stderr at the end.
  - Given `--fail-fast`, processing stops immediately after the first failure and exit code is 1.
  - Given batch processing is running and stdout is a TTY, a progress bar showing `X/N files complete` is displayed on stderr.
  - Given stdout is not a TTY (piped), the progress bar is not displayed.

**US-9** — As a content creator, I want to list available voices so that I know what voices I can use.
- Acceptance Criteria:
  - Given `supertone voices list`, a table with columns Name, ID, Type, and Supported Languages is printed to stdout.
  - Given `--type preset`, only preset voices are displayed.
  - Given `--type custom`, only custom (user-created) voices are displayed.
  - Given `--format json`, output is a valid JSON array where each object contains at minimum `name`, `id`, `type`, and `languages` fields.

**US-13** — As a user, I want to set my API key once so that I do not need to enter it on every command.
- Acceptance Criteria:
  - Given `supertone config set api_key <key>`, the key is written to `~/.config/supertone/config.toml`.
  - Given the config file is created or modified, its file permissions are set to `600` (owner read/write only).
  - Given `SUPERTONE_API_KEY` environment variable is set, it takes precedence over the value in `config.toml`.
  - Given neither env var nor config file key is present, any command requiring authentication exits with code 2 and instructs the user to run `supertone config set api_key` or set `SUPERTONE_API_KEY`.

**US-15** — As a user, I want to check my API usage so that I can manage my costs.
- Acceptance Criteria:
  - Given `supertone usage`, the current usage, remaining credits, and plan information are displayed in human-readable format.
  - Given `--format json`, the same data is returned as a valid JSON object.
  - Given the API call fails, exit code is 1 and the error is printed to stderr.

### Should

**US-4** — As a content creator, I want to preview the expected audio duration before generating so that I can conserve credits.
- Acceptance Criteria:
  - Given `supertone tts predict "text"`, the predicted duration in seconds and estimated credit cost are printed to stdout.
  - Given `--input script.txt`, the file contents are used for prediction.
  - Given `cat script.txt | supertone tts predict`, stdin input is accepted.
  - Given `--format json`, output is a valid JSON object with at minimum `duration_seconds` and `estimated_credits` fields.
  - Given the prediction API does not deduct credits, no credits are consumed by this command.

**US-8** — As a pipeline builder, I want to receive metadata as JSON so that my scripts can parse the output.
- Acceptance Criteria:
  - Given `--format json` on any non-audio-output command, the response is valid JSON printed to stdout.
  - Given `--format json` on `supertone tts`, the JSON output contains at minimum `output_file`, `duration_seconds`, and `voice_id` fields; audio bytes are NOT included in the JSON.
  - Given `--format json`, no table or human-readable formatting is mixed into stdout.

**US-10** — As a content creator, I want to search voices by language, gender, age, and use case so that I can find the right voice quickly.
- Acceptance Criteria:
  - Given `--lang ko`, only voices supporting Korean are returned.
  - Given `--gender female`, only female voices are returned.
  - Given `--age young`, only voices tagged as young are returned.
  - Given `--use-case narration`, only voices suited for narration are returned.
  - Given `--query "밝은"`, voices matching the keyword are returned.
  - Given multiple filters, results satisfy all filters simultaneously (AND logic).
  - Given `--format json`, results are returned as a valid JSON array.

**US-14** — As a user, I want to save frequently used settings as defaults so that I can avoid repetitive input.
- Acceptance Criteria:
  - Given `supertone config set default_voice <id>`, subsequent `supertone tts` commands without `--voice` use this ID.
  - Given `supertone config set default_model sona_speech_2`, subsequent `supertone tts` commands without `--model` use this model.
  - Given `supertone config set default_lang ko`, subsequent `supertone tts` commands without `--lang` use `ko`.
  - Given `supertone config get api_key`, the stored key value is printed (not masked, see Assumptions A-3).
  - Given `supertone config list`, all stored key-value pairs are printed.
  - Given `supertone config init`, an interactive prompt collects API key, default voice, default model, and default language, then writes them to `config.toml`.

**US-11** — As a content creator, I want to create a custom voice from my audio sample so that I can use a unique brand voice.
- Acceptance Criteria:
  - Given `supertone voices clone --name "my-narrator" --sample ./voice_sample.wav`, the sample file is uploaded and a `voice_id` is printed to stdout on success.
  - Given `--sample` points to an unsupported audio format, exit code is 3 and an error message listing supported formats is printed before any upload attempt.
  - Given `--format json`, the output is a valid JSON object containing at minimum `voice_id` and `name` fields.
  - Given the cloned voice ID is returned, it can immediately be used with `supertone tts --voice <id>`.

**US-12** — As a content creator, I want to distinguish preset voices from custom voices so that I can manage my created voices.
- Acceptance Criteria:
  - Given `supertone voices list`, the Type column clearly distinguishes `preset` from `custom`.
  - Given `supertone voices list --type custom`, only user-created voices are shown.

### Could

**US-3 (streaming)** — As a pipeline builder, I want real-time audio playback while the audio is being generated so that I can preview results without waiting for full generation.
- Acceptance Criteria:
  - Given `--stream` and model is `sona_speech_1`, audio is played to the system audio output in real time as chunks arrive.
  - Given `--stream` and model is NOT `sona_speech_1`, exit code is 3 and an error message states that streaming is only supported with `sona_speech_1`.
  - Given `--stream` and `--output <file>`, audio is simultaneously saved to the file and played to audio output.

---

## Functional Requirements

### FR-001: TTS Command — Text Input and Output

**Description**: The `supertone tts` command converts text to speech audio. It accepts input from three sources (positional argument, `--input` file, stdin) and writes output to a file, `--outdir`, or stdout.

**Priority**: Must

**Acceptance Criteria**:
- Exactly one input source must be active. Providing more than one exits with code 3.
- Given positional text argument, that text is used as input.
- Given `--input <file>` pointing to an existing non-empty file, file contents are used.
- Given stdin piped and no positional argument or `--input`, stdin contents are used.
- Given `--output <path>`, audio is written to that path.
- Given `--output -`, audio bytes are written to stdout with no other bytes on stdout.
- Given no `--output`, audio is written to `output.<format>` in the current working directory (default format: `wav`).
- Given `--output-format mp3`, the API receives the mp3 format parameter and the output file extension matches.

**Dependencies**: FR-008 (config for default values), FR-009 (error handling)

---

### FR-002: TTS Command — Voice and Audio Parameters

**Description**: The `supertone tts` command exposes all SDK audio parameters as CLI flags.

**Priority**: Must

**Accepted options and their defaults**:

| Flag | Type | Default | Notes |
|------|------|---------|-------|
| `--voice` | string | `default_voice` from config or required | |
| `--model` | enum | `sona_speech_2` | `sona_speech_1`, `supertonic_api_1`, `supertonic_api_3`, `sona_speech_2`, `sona_speech_2_flash`, `sona_speech_2t` |
| `--lang` | string | `ko` | Language code |
| `--style` | string | model default | SDK style parameter |
| `--output-format` | enum | `wav` | `wav`, `mp3`, `ogg`, `flac`, `aiff` |
| `--speed` | float | model default | |
| `--pitch` | float | model default | |
| `--pitch-variance` | float | model default | |
| `--similarity` | float | model default | Not supported on `sona_speech_2_flash` |
| `--text-guidance` | float | model default | Not supported on `sona_speech_2_flash` |
| `--stream` | bool | false | Only supported on `sona_speech_1` |
| `--include-phonemes` | bool | false | |

**Acceptance Criteria**:
- Given `--model sona_speech_2_flash` and `--similarity` is provided, exit code is 3 and an error message states the parameter is not supported by that model.
- Given `--model sona_speech_2_flash` and `--text-guidance` is provided, exit code is 3 and an error message states the parameter is not supported by that model.
- Given `--model supertonic_api_1` or `--model supertonic_api_3` and any parameter other than `--speed` is provided (excluding `--voice`, `--lang`, `--output-format`), the unsupported parameter is silently ignored OR an exit-code-3 error is raised. (See Assumption A-4.)
- Given `--model supertonic_api_3`, the SDK exposes 31 languages (`ar, bg, cs, da, de, el, en, es, et, fi, fr, hi, hr, hu, id, it, ja, ko, lt, lv, nl, pl, pt, ro, ru, sk, sl, sv, tr, uk, vi`); `--lang` is validated against the SDK enum.
- Given `--stream` and model is not `sona_speech_1`, exit code is 3.
- Given `--include-phonemes true`, phoneme data is included in the response and written alongside the audio output. (See Assumption A-5 for output format.)

**Dependencies**: FR-001, FR-008

---

### FR-003: TTS Predict Subcommand

**Description**: `supertone tts predict` calls the Predict Duration API and reports estimated audio duration and credit cost without generating audio or consuming credits.

**Priority**: Should

**Acceptance Criteria**:
- Given `supertone tts predict "text"`, predicted duration (seconds) and estimated credit cost are printed to stdout.
- Given `--input <file>`, file contents are used.
- Given stdin piped, stdin contents are used.
- Given `--format json`, output is a JSON object with at minimum `duration_seconds` (number) and `estimated_credits` (number) fields.
- No audio file is created.
- No credits are deducted from the account.
- The same `--voice`, `--model`, `--lang` options accepted by `supertone tts` are accepted here to produce an accurate estimate.

**Dependencies**: FR-001, FR-002

---

### FR-004: Batch Processing

**Description**: `supertone tts` processes multiple input files when `--input` is a directory or glob pattern and `--outdir` is specified.

**Priority**: Must

**Acceptance Criteria**:
- Given `--input ./scripts/ --outdir ./audio/`, all `.txt` files directly inside `./scripts/` are processed (see Assumption A-6 for subdirectory handling).
- Given `--input "scripts/*.txt" --outdir ./audio/`, all glob-matched files are processed.
- Given input file `script1.txt`, the output file is named `script1.<output-format>` in `--outdir`.
- Given `--outdir` does not exist, it is created before processing begins.
- Given a file fails to process, the error is logged to stderr and processing continues with the next file.
- Given `--fail-fast`, processing halts on the first failure and exit code is 1.
- Given batch is running and stdout is a TTY, a progress indicator showing `X / N` files is rendered on stderr.
- Given stdout is not a TTY, the progress indicator is suppressed.
- A summary line `N succeeded, M failed` is printed to stderr after all files are processed.

**Dependencies**: FR-001, FR-002, FR-009

---

### FR-005: Voices List Command

**Description**: `supertone voices list` retrieves and displays all voices available to the authenticated user.

**Priority**: Must

**Acceptance Criteria**:
- Given `supertone voices list`, a table with columns Name, ID, Type, Supported Languages is printed to stdout.
- Given `--type preset`, only voices with type `preset` are displayed.
- Given `--type custom`, only voices with type `custom` are displayed.
- Given `--format json`, output is a valid JSON array; each element contains at minimum `name` (string), `id` (string), `type` (string), `languages` (array of strings).
- Given the API returns zero voices, an empty table (with headers) or empty JSON array is returned and exit code is 0.

**Dependencies**: FR-009

---

### FR-006: Voices Search Command

**Description**: `supertone voices search` filters available voices using one or more search criteria.

**Priority**: Should

**Acceptance Criteria**:
- Given `--lang ko`, only voices with Korean in their supported language list are returned.
- Given `--gender female`, only female voices are returned.
- Given `--age young`, only voices tagged young are returned.
- Given `--use-case narration`, only voices tagged for narration use are returned.
- Given `--query "밝은"`, voices matching the keyword are returned.
- Given multiple filters, only voices matching ALL specified filters are returned.
- Given `--format json`, output is a valid JSON array matching the same schema as FR-005.
- Given no results match the filters, an empty table or empty JSON array is returned and exit code is 0.

**Dependencies**: FR-009

---

### FR-007: Voices Clone Command

**Description**: `supertone voices clone` registers a custom voice from a local audio sample file.

**Priority**: Should

**Acceptance Criteria**:
- Given `--name "my-narrator" --sample ./sample.wav`, the file is uploaded to the Voice Cloning Registration API.
- Given the upload succeeds, the resulting `voice_id` is printed to stdout.
- Given `--format json`, a JSON object with at minimum `voice_id` (string) and `name` (string) is printed.
- Given `--sample` points to a file with an unsupported audio format, exit code is 3, a message listing supported formats is printed to stderr, and no upload is attempted.
- Given the upload fails, exit code is 1 and the error is printed to stderr.
- The registered voice is immediately usable via `supertone tts --voice <voice_id>`.

**Open item**: Supported upload audio formats are not enumerated in the PRD. See Assumption A-7.

**Dependencies**: FR-009

---

### FR-008: Config Command

**Description**: `supertone config` manages the persistent configuration file at `~/.config/supertone/config.toml`.

**Priority**: Must

**Subcommands**:

| Subcommand | Description |
|------------|-------------|
| `config init` | Interactive prompt: sets `api_key`, `default_voice`, `default_model`, `default_lang` |
| `config set <key> <value>` | Sets a single configuration key |
| `config get <key>` | Prints the current value of a single key |
| `config list` | Prints all stored key-value pairs |

**Acceptance Criteria**:
- Given `supertone config set api_key <key>`, the key is written to `~/.config/supertone/config.toml` under the `api_key` field.
- Given the config file is created or written, the file permissions are set to `600` immediately after the write.
- Given `SUPERTONE_API_KEY` environment variable is set, it is used in preference to the `api_key` field in `config.toml` for all commands.
- Given `supertone config init`, the user is prompted interactively for `api_key`, `default_voice`, `default_model`, and `default_lang`; pressing Enter without input retains any existing value.
- Given `supertone config get <key>` and the key exists, its value is printed to stdout.
- Given `supertone config get <key>` and the key does not exist, exit code is 3 and an error message names the missing key.
- Given `supertone config list`, all key-value pairs in `config.toml` are printed to stdout.
- Given `config.toml` does not exist, `config list` prints an empty result and `config get` exits with code 3.
- The API key must NOT appear in any log line, error message, or exception traceback.

**Valid settable keys**: `api_key`, `default_voice`, `default_model`, `default_lang`

**Dependencies**: NFR-003

---

### FR-009: Output and Error Handling

**Description**: All commands follow a consistent output routing and exit code convention.

**Priority**: Must

**Acceptance Criteria**:

Exit codes:
- `0` — success
- `1` — general error (API error, network error, unexpected exception)
- `2` — authentication error (missing or invalid API key)
- `3` — input/usage error (bad arguments, missing required options, unsupported parameter combinations)

Output routing:
- Human-readable text (tables, progress bars, status messages) is written to stderr.
- Structured data (audio bytes, JSON output) is written to stdout.
- Given `--format json`, no human-readable formatting is mixed into stdout.
- All error messages are written to stderr.
- Given stdout is not a TTY (piped or redirected), progress indicators and ANSI color codes are automatically disabled.

Error messages:
- Every error message states the cause and at least one corrective action.
- The API key value is never included in any error message or traceback.

**Dependencies**: none

---

### FR-010: Usage Command

**Description**: `supertone usage` retrieves and displays the authenticated user's API usage summary.

**Priority**: Should

**Acceptance Criteria**:
- Given `supertone usage`, usage quantity, remaining credits, and plan name are displayed in human-readable format on stdout.
- Given `--format json`, a valid JSON object with at minimum `used` (number), `remaining` (number), and `plan` (string) fields is printed.
- Given the API call fails, exit code is 1 and the error is printed to stderr.

**Dependencies**: FR-009

---

## Non-Functional Requirements

### NFR-001: Installability

**Description**: The CLI must be installable from PyPI without additional system dependencies beyond Python.

**Priority**: Must

**Measurable targets**:
- `pip install supertone-cli` completes successfully on Python 3.11, 3.12, and 3.13 on macOS and Linux.
- PyPI installation success rate target: > 95% (measured via PyPI download statistics).
- Required runtime dependencies limited to: `supertone` (SDK), `typer`, `rich`. No other third-party packages unless justified.
- Time from `pip install supertone-cli` to successful first TTS output: < 3 minutes in user testing.

---

### NFR-002: CLI Startup Latency

**Description**: The CLI must start fast enough to feel native in a shell environment.

**Priority**: Must

**Measurable targets**:
- `time supertone --help` completes in < 500ms on a standard developer machine (measured as wall-clock time on a machine with Python 3.11+ and all dependencies installed).
- This target applies to the CLI process startup and argument parsing only; TTS API response time is excluded.
- Import optimization (lazy imports) must be applied to any module that is not needed at startup.

---

### NFR-003: Security — API Key Handling

**Description**: The API key must be stored and transmitted securely and must not be exposed in logs or error output.

**Priority**: Must

**Measurable targets**:
- `config.toml` file permissions are verified to be `600` after every write operation; any permission other than `600` is treated as a test failure.
- Zero occurrences of the API key string in any stderr output, log file, or exception traceback (verified by automated test with a known dummy key).
- `SUPERTONE_API_KEY` environment variable overrides `config.toml` in 100% of cases.
- The API key is transmitted only via HTTPS to the Supertone API endpoint.

---

### NFR-004: Test Coverage

**Description**: The codebase must have sufficient automated test coverage to support confident refactoring and regression detection.

**Priority**: Must

**Measurable targets**:
- Overall line coverage measured by `pytest-cov`: > 80%.
- Every subcommand (tts, tts predict, voices list, voices search, voices clone, usage, config init/set/get/list) has at minimum one passing unit test.
- All tests that call the Supertone API are mocked using `unittest.mock` or equivalent; no test in the default `pytest` run makes a real network call.
- Integration tests that make real API calls are tagged `@pytest.mark.integration` and excluded from the default `pytest` run.
- Tests are runnable with `uv run pytest -q` without additional setup beyond environment variables.

---

### NFR-005: Observability — Exit Code Consistency

**Description**: Exit codes must be machine-readable and consistent to enable reliable scripting.

**Priority**: Must

**Measurable targets**:
- Exit code contract (0, 1, 2, 3) is enforced by automated tests that check `subprocess` return codes for representative success and failure scenarios.
- Any unhandled exception that reaches the top-level handler must result in exit code 1, never 0.

---

## Out of Scope

The following are explicitly excluded from Phase 1:

| Item | Deferred to |
|------|------------|
| Emotion/style system (fine-grained emotional direction) | Phase 2 |
| Non-verbal tag auto-insertion | Phase 2 |
| Voice guiding | Phase 2 |
| Script format parser (scene/character markup) | Phase 2 |
| YAML workflow orchestration | Phase 2 |
| Profile/preset system (`--profile narrator`) | Phase 2 |
| GUI or TUI interface | Out of scope indefinitely |
| `supertone models` command (models are fixed at 4, documented in `--help`) | Dropped by PRD decision |
| Audio post-processing (normalization, trimming, mixing) | Not stated in PRD |
| Multi-speaker / conversation audio generation | Not stated in PRD |
| Speech-to-text (STT) | Not stated in PRD |
| Dubbing | Not stated in PRD |

---

## Assumptions

**A-1**: The PRD states `--lang` supports "23개" languages but the brainstorm notes describe SONA Speech 2 as supporting "24개 언어". The exact supported language count and the full list of language codes are not enumerated in the PRD. This requirements document assumes the SDK documentation is the authoritative source. **Verify with Supertone SDK docs before implementation.**

**A-2**: The PRD says `--format json` applies to `supertone tts` but does not define what JSON output means when the primary output is binary audio. This document assumes that `--format json` on `supertone tts` returns a JSON metadata object (containing `output_file`, `duration_seconds`, `voice_id`, and `characters_processed`) while audio is written to the file specified by `--output` (not stdout). Using `--format json` with `--output -` (stdout audio) is treated as an input error (exit code 3). **Verify with stakeholder.**

**A-3**: `supertone config get api_key` behavior is not defined regarding masking. This document assumes the full key is returned unmasked since the command is explicit and the user is authenticated at the OS level by the `600` file permission. **Verify with stakeholder — masking may be preferred.**

**A-4**: The PRD states `supertonic_api_1` (and `supertonic_api_3`) supports only `--speed` for audio adjustment. The behavior when other audio parameters (`--pitch`, `--similarity`, etc.) are passed with these models is not specified. This document flags this as ambiguous. **Recommend: raise exit code 3 with a clear message listing unsupported parameters for the model.**

**A-5**: The behavior of `--include-phonemes true` regarding output is not specified. The PRD does not state whether phoneme data is printed to stdout, written to a sidecar file, or embedded in the JSON response. **Verify with stakeholder before implementing.**

**A-6**: Batch processing with `--input ./scripts/` is not specified for recursive subdirectory traversal. This document assumes non-recursive (top-level `.txt` files only) as the default, with no `--recursive` flag in Phase 1. **Verify with stakeholder.**

**A-7**: The supported audio formats for `voices clone --sample` upload are not enumerated in the PRD (only "~10 seconds" sample duration guidance is given). This document assumes the supported formats are determined by the SDK/API specification. **The list of valid upload formats must be sourced from SDK documentation before implementing the pre-upload validation check.**

**A-8**: The PRD Decision #3 states that `--stream` allows "simultaneous file save" but no flag or mechanism for this is defined. This document assumes that when both `--stream` and `--output <file>` are provided together, audio is simultaneously played and written to the file. When `--stream` is used without `--output`, audio is played only. **Verify this behavior with stakeholder.**

**A-9**: The PRD does not specify the maximum text length accepted by the CLI per invocation. Rate limits and text-length limits are assumed to be enforced by the API; the CLI passes input as-is and propagates API errors.

**A-10**: The config file path `~/.config/supertone/config.toml` is fixed. The PRD does not mention a `--config` flag to override this path. This is assumed Out of Scope for Phase 1.

---

## Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|-----------|
| R-1 | Supertone SDK API surface changes (method signatures, error classes) between PRD authoring and implementation, requiring rework | Medium | High | Pin SDK version in `pyproject.toml`; abstract SDK calls behind a `client.py` wrapper layer as specified in the PRD package structure |
| R-2 | The Supertone API is in beta; endpoints may be unstable or rate-limited in ways not documented, causing flaky integration tests | Medium | Medium | Separate unit tests (mocked) from integration tests (`-m integration`); integration test failures do not block CI by default |
| R-3 | Streaming audio playback (`--stream`) depends on the host system's audio output capabilities; no audio library is specified in the PRD dependencies | Medium | Medium | PRD lists only `supertone`, `typer`, `rich` as dependencies. An audio playback library (e.g., `sounddevice`, `pyaudio`) will be needed. **Must be confirmed and added to dependencies before implementation.** |
| R-4 | `--output -` (stdout audio) combined with `--format json` creates an impossible dual-output state; users may attempt this combination | Low | Low | Detect at argument parsing stage and exit with code 3 before any API call |
| R-5 | Test coverage target of > 80% may be difficult to achieve for interactive `config init` prompts and streaming playback code paths | Low | Medium | Use dependency injection for the interactive prompt and audio playback layer to enable mocking in unit tests |
| R-6 | Glob pattern expansion behavior differs between shells (zsh, bash) and Python's `glob` module; users may pass unquoted globs that the shell expands before the CLI receives them | Low | Low | Document that glob patterns passed to `--input` should be quoted; validate the pattern in the CLI and emit a warning if no files are matched |

---

## Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|--------------------|
| Install to first TTS output | < 3 minutes | User testing session with a new user and a fresh environment |
| CLI startup time (`supertone --help`) | < 500ms p95 | Automated benchmark: 100 consecutive runs, measure wall-clock time |
| Test line coverage | > 80% | `uv run pytest --cov=src --cov-report=term-missing` in CI |
| PyPI installation success rate | > 95% | PyPI download statistics; installation failures reported via issue tracker |
| API key exposure incidents | 0 | Automated test: run each error path with a known dummy key, assert key string absent from all output |
