# Issues — Supertone CLI (Phase 1)

**Generated**: 2026-04-03
**Source**: PRD Digest, Requirements v1.0, UX Spec v1.0, Architecture v1.0

---

## Dependency Graph (Critical Path)

```
ISSUE-001 (scaffold)
    |
    v
ISSUE-002 (errors + output)
    |
    +---> ISSUE-003 (config module + config commands)
    |         |
    |         v
    |     ISSUE-004 (client wrapper)
    |         |
    |         +---> ISSUE-005 (tts command - single)
    |         |         |
    |         |         +---> ISSUE-006 (tts params + validation)
    |         |         |         |
    |         |         |         +---> ISSUE-007 (batch processing)
    |         |         |         +---> ISSUE-010 (tts predict)
    |         |         |         +---> ISSUE-013 (streaming TTS)
    |         |         |
    |         |         +---> ISSUE-007 (batch processing)
    |         |
    |         +---> ISSUE-008 (voices list)
    |         +---> ISSUE-009 (voices search)  [parallel with 008]
    |         +---> ISSUE-011 (voices clone)   [parallel with 008]
    |         +---> ISSUE-012 (usage command)   [parallel with 008]
    |
    +---> ISSUE-014 (lazy imports + startup benchmark) [after ISSUE-005]
    +---> ISSUE-015 (CI pipeline) [after ISSUE-005]
```

**Parallel tracks after ISSUE-004:**
- Track A: TTS commands (005 -> 006 -> 007, 010, 013)
- Track B: Voice commands (008, 009, 011 — all parallel)
- Track C: Usage command (012)
- Track D: Polish (014, 015)

---

### ISSUE-001: Scaffold project with uv, pyproject.toml, and package structure
- Track: platform
- UI: false
- Manual: false
- PRD-Ref: NFR-001
- Priority: P0
- Estimate: 0.5d
- Status: done
- Owner:
- Branch: issue/ISSUE-001-scaffold
- GH-Issue: https://github.com/pillip/supertone-cli/issues/1
- PR: https://github.com/pillip/supertone-cli/pull/2
- Depends-On: none

#### Goal
A working Python package exists that can be installed with `pip install -e .` and exposes the `supertone` CLI entry point that prints help text.

#### Scope (In/Out)
- In: `pyproject.toml` with project metadata, dependencies (typer, rich, tomli_w, supertone SDK stub), optional extras (stream: sounddevice), `[project.scripts]` entry point, `src/supertone_cli/` package directory with `__init__.py`, empty module files for all 7 modules (`cli.py`, `config.py`, `client.py`, `output.py`, `errors.py`, `commands/__init__.py`, `commands/tts.py`, `commands/voices.py`, `commands/usage.py`, `commands/config_cmd.py`), `tests/` directory with `conftest.py`, pytest config in `pyproject.toml`, ruff config
- Out: Any command logic beyond `--help` and `--version`

#### Acceptance Criteria (DoD)
- [ ] Given the repo is cloned, when `uv sync` is run, then all dependencies are installed without errors
- [ ] Given dependencies are installed, when `uv run supertone --help` is run, then help text is printed to stdout and exit code is 0
- [ ] Given dependencies are installed, when `uv run supertone --version` is run, then the version string is printed and exit code is 0
- [ ] Given the project structure, when `uv run pytest -q` is run, then tests pass (at minimum a smoke test)
- [ ] Given `pyproject.toml`, then `supertone-cli` is the package name, Python `>=3.11` is required, and `supertone` is the console script entry point

#### Implementation Notes
- Use `uv init` then customize `pyproject.toml`
- Entry point: `supertone_cli.cli:main`
- Typer app in `cli.py` with `app = typer.Typer()` and `--version` callback
- All command modules are empty stubs (will be filled in subsequent issues)
- Follow `src/` layout per architecture doc

#### Tests
- [ ] Smoke test: import `supertone_cli` succeeds
- [ ] CLI test: `supertone --help` exits with code 0
- [ ] CLI test: `supertone --version` prints version string

#### Rollback
Delete the branch. No persistent state created.

---

### ISSUE-002: Implement error hierarchy and output formatting module
- Track: product
- UI: true
- Manual: false
- PRD-Ref: FR-009, NFR-005
- Priority: P0
- Estimate: 1d
- Status: done
- Owner:
- Branch: issue/ISSUE-002-errors-output
- GH-Issue: https://github.com/pillip/supertone-cli/issues/3
- PR: https://github.com/pillip/supertone-cli/pull/4
- Depends-On: ISSUE-001

#### Goal
The `errors.py` and `output.py` modules are fully implemented, providing consistent error handling with exit codes and output formatting (tables, JSON, progress, TTY detection) used by all subsequent commands.

#### Scope (In/Out)
- In: `errors.py` — `CLIError(exit_code=1)`, `AuthError(exit_code=2)`, `InputError(exit_code=3)`, `APIError(exit_code=1)`; top-level exception handler in `cli.py` that catches `CLIError` subclasses and calls `sys.exit()`; `output.py` — `print_table()`, `print_json()`, `print_error()`, `create_progress()`, `is_pipe()`, `NO_COLOR` support, TTY detection
- Out: Data models (in data_model), command implementations

#### Acceptance Criteria (DoD)
- [ ] Given an `AuthError` is raised, when the top-level handler catches it, then exit code is 2 and the error message is printed to stderr in the format `Error: <cause>. <fix>.`
- [ ] Given an `InputError` is raised, when caught, then exit code is 3
- [ ] Given an `APIError` is raised, when caught, then exit code is 1
- [ ] Given an unhandled exception reaches the top-level handler, then exit code is 1 and the API key (if present in the exception message) is stripped from the output
- [ ] Given stdout is not a TTY, when `is_pipe()` is called, then it returns `True`
- [ ] Given `NO_COLOR` env var is set, when output functions are called, then ANSI color codes are not emitted
- [ ] Given `print_json(data)` is called, when data is a dict or list, then valid JSON is written to stdout with no extra formatting
- [ ] Given `print_table(headers, rows)` is called, then a Rich table is rendered to stderr

#### Implementation Notes
- `errors.py`: Define exception hierarchy per architecture doc. Add a `sanitize_message(msg, api_key)` function that strips the API key from any string.
- `output.py`: Use `rich.console.Console(stderr=True)` for human output. `is_pipe()` checks `sys.stdout.isatty()`. `print_json` uses `json.dumps(data, indent=2, ensure_ascii=False)`.
- Top-level handler in `cli.py`: wrap `app()` call in try/except for `CLIError`, `KeyboardInterrupt`, `BrokenPipeError`.

#### Tests
- [ ] Unit: `CLIError`, `AuthError`, `InputError`, `APIError` have correct `exit_code` attributes
- [ ] Unit: `sanitize_message("key is sk-abc123", "sk-abc123")` returns `"key is ***"`
- [ ] Unit: `print_json({"a": 1})` writes valid JSON to stdout
- [ ] Unit: `is_pipe()` returns correct value (mock `sys.stdout.isatty`)
- [ ] Integration: subprocess test raising `AuthError` exits with code 2
- [ ] Integration: subprocess test with unhandled exception exits with code 1

#### Rollback
Revert the branch. No persistent state.

---

### ISSUE-003: Implement config module and config commands (init/set/get/list)
- Track: product
- UI: false
- Manual: false
- PRD-Ref: FR-008, NFR-003, US-13, US-14
- Priority: P0
- Estimate: 1.5d
- Status: done
- Owner:
- Branch: issue/ISSUE-003-config
- GH-Issue: https://github.com/pillip/supertone-cli/issues/5
- PR: https://github.com/pillip/supertone-cli/pull/6
- Depends-On: ISSUE-002

#### Goal
The `config.py` module reads/writes `~/.config/supertone/config.toml` with 600 permissions, resolves env var overrides, and the `config` command group (init/set/get/list) is fully functional.

#### Scope (In/Out)
- In: `config.py` — `load_config()`, `save_config()`, `get_api_key()`, `get_default()`, `CONFIG_PATH`, `VALID_CONFIG_KEYS`; `commands/config_cmd.py` — `init`, `set_value`, `get_value`, `list_values` subcommands; config file creation with `0o600` permissions; env var `SUPERTONE_API_KEY` override; interactive `config init` prompt; key validation (reject unknown keys, reject empty `api_key`)
- Out: Other command implementations, masking in `config list` (stretch)

#### Acceptance Criteria (DoD)
- [ ] Given `supertone config set api_key sk-test123`, when the command completes, then `~/.config/supertone/config.toml` contains `api_key = "sk-test123"` and file permissions are `0o600`
- [ ] Given `supertone config set foo bar`, when the command runs, then exit code is 3 with message listing valid keys
- [ ] Given `supertone config set api_key ""`, when the command runs, then exit code is 3 with a non-empty-required message
- [ ] Given `supertone config get default_voice` and the key is set, then the value is printed to stdout
- [ ] Given `supertone config get default_voice` and the key is not set, then exit code is 3
- [ ] Given `supertone config list`, then all key-value pairs are printed; `api_key` is masked in list output
- [ ] Given config file does not exist, when `config list` runs, then empty output with exit code 0
- [ ] Given `SUPERTONE_API_KEY=sk-env` is set, when `get_api_key()` is called, then `sk-env` is returned regardless of config file content
- [ ] Given `supertone config init` in a TTY, when user enters values, then config file is written with all provided values and permissions are `0o600`
- [ ] Given `supertone config init` with stdin piped (not TTY), then exit code is 3 with message to use `config set` instead

#### Implementation Notes
- `config.py`: Use `tomllib.load()` for reading, `tomli_w.dump()` for writing. `Path.chmod(0o600)` after every write. Create parent dir with `mkdir(parents=True, exist_ok=True)`.
- `commands/config_cmd.py`: Register as `config_app = typer.Typer()` added to main app. `config init` uses `typer.prompt()` or `rich.prompt.Prompt`.
- Resolution order: CLI flags > env vars > config file > defaults. `get_api_key()` checks `os.environ.get("SUPERTONE_API_KEY")` first.
- Valid keys: `VALID_CONFIG_KEYS = {"api_key", "default_voice", "default_model", "default_lang"}`

#### Tests
- [ ] Unit: `save_config({"api_key": "test"})` creates TOML file with correct content and `0o600` permissions
- [ ] Unit: `load_config()` returns dict from existing TOML file
- [ ] Unit: `load_config()` returns empty dict when file does not exist
- [ ] Unit: `get_api_key()` returns env var value when set (mock `os.environ`)
- [ ] Unit: `get_api_key()` returns config file value when env var not set
- [ ] Unit: `get_api_key()` returns `None` when neither is set
- [ ] CLI test: `config set` + `config get` round-trip
- [ ] CLI test: `config set` with invalid key exits 3
- [ ] CLI test: `config list` with no config file exits 0

#### Rollback
Revert the branch. Delete any test config files created during testing (use tmp dirs in tests).

---

### ISSUE-004: Implement SDK client wrapper module
- Track: platform
- UI: false
- Manual: false
- PRD-Ref: FR-001, FR-003, FR-005, FR-006, FR-007, FR-010
- Priority: P0
- Estimate: 1d
- Status: done
- Owner:
- Branch: issue/ISSUE-004-client
- GH-Issue: https://github.com/pillip/supertone-cli/issues/7
- PR: https://github.com/pillip/supertone-cli/pull/8
- Depends-On: ISSUE-003

#### Goal
The `client.py` module provides a thin wrapper over the Supertone SDK, is the only module that imports `supertone`, translates SDK exceptions into CLI errors, and exposes all 7 SDK operations as typed functions.

#### Scope (In/Out)
- In: `client.py` — `get_client()` lazy singleton, `create_speech()`, `stream_speech()`, `predict_duration()`, `list_voices()`, `search_voices()`, `clone_voice()`, `get_usage()`; SDK exception translation to `AuthError`/`APIError`; data models (`Voice`, `Usage`, `Prediction`, `CloneResult`, `TTSResult`, `BatchResult`, `BatchError`) in `models.py` or `client.py`
- Out: Command implementations that call these functions, actual API calls (all tests use mocks)

#### Acceptance Criteria (DoD)
- [ ] Given a valid API key in config, when `get_client()` is called, then a Supertone SDK client instance is returned (lazy, singleton per process)
- [ ] Given no API key, when `get_client()` is called, then `AuthError` is raised with exit code 2 and a message instructing the user to set the key
- [ ] Given `create_speech(text, voice, model, lang)` is called, when the SDK returns audio bytes, then raw bytes are returned
- [ ] Given `create_speech()` is called and the SDK raises an auth error, then `AuthError` is raised
- [ ] Given `create_speech()` is called and the SDK raises a network/server error, then `APIError` is raised
- [ ] Given `list_voices()` is called, then a list of `Voice` dataclass instances is returned
- [ ] Given data models are defined, then `Voice`, `Usage`, `Prediction`, `CloneResult`, `TTSResult`, `BatchResult`, `BatchError` are importable from the models module

#### Implementation Notes
- `client.py` is the ONLY module that `import supertone`. Use lazy import inside functions, not at module level (NFR-002 startup latency).
- SDK exception mapping: inspect the SDK's exception hierarchy. Common pattern: `supertone.AuthenticationError` -> `AuthError`, `supertone.APIError` -> `APIError`.
- Data models: frozen dataclasses as specified in `docs/data_model.md`. Place in `src/supertone_cli/models.py`.
- `get_client()` uses a module-level `_client` variable for singleton.

#### Tests
- [ ] Unit: `get_client()` with mocked config returning an API key creates client (mock SDK constructor)
- [ ] Unit: `get_client()` with no API key raises `AuthError`
- [ ] Unit: `create_speech()` returns bytes when SDK succeeds (mock SDK)
- [ ] Unit: `create_speech()` raises `AuthError` when SDK auth fails (mock SDK)
- [ ] Unit: `create_speech()` raises `APIError` when SDK returns server error (mock SDK)
- [ ] Unit: `list_voices()` returns list of `Voice` dataclasses (mock SDK)
- [ ] Unit: `predict_duration()` returns `Prediction` dataclass (mock SDK)
- [ ] Unit: `clone_voice()` returns `CloneResult` dataclass (mock SDK)
- [ ] Unit: `get_usage()` returns `Usage` dataclass (mock SDK)
- [ ] Unit: Data models are frozen dataclasses with correct fields

#### Rollback
Revert the branch.

---

### ISSUE-005: Implement single TTS command (text/file/stdin input, file/stdout output)
- Track: product
- UI: false
- Manual: false
- PRD-Ref: FR-001, US-1, US-2, US-5, US-6
- Priority: P0
- Estimate: 1.5d
- Status: done
- Owner:
- Branch: issue/ISSUE-005-tts
- GH-Issue: https://github.com/pillip/supertone-cli/issues/9
- PR: https://github.com/pillip/supertone-cli/pull/10
- Depends-On: ISSUE-004

#### Goal
`supertone tts "text"` generates an audio file from text input (positional arg, `--input` file, or stdin) and writes to a file or stdout, with correct input source disambiguation and output routing.

#### Scope (In/Out)
- In: `commands/tts.py` — `tts` command with positional TEXT arg, `--input`, `--output`, `--output-format`, `--voice`, `--model`, `--lang`, `--format` (text/json); input source resolution (exactly one of: positional, file, stdin); output routing (file, stdout with `--output -`, default `output.<format>`); spinner on stderr during generation (TTY only); success message on stderr; `--format json` metadata output; register tts command group in `cli.py`
- Out: Batch processing, parameter validation beyond basic, streaming, predict subcommand

#### Acceptance Criteria (DoD)
- [ ] Given `supertone tts "Hello" --voice v1`, when the API returns audio, then `output.wav` is created in the current directory and exit code is 0
- [ ] Given `supertone tts "Hello" --voice v1 --output hello.wav`, then `hello.wav` is created
- [ ] Given `supertone tts "Hello" --voice v1 --output-format mp3`, then `output.mp3` is created
- [ ] Given `supertone tts --input script.txt --voice v1`, when `script.txt` exists and is non-empty, then its contents are sent to the API
- [ ] Given `supertone tts --input script.txt` and the file does not exist, then exit code is 3
- [ ] Given `supertone tts --input script.txt` and the file is empty, then exit code is 3
- [ ] Given `echo "Hello" | supertone tts --voice v1`, then piped stdin text is used as input
- [ ] Given both positional text and `--input` are provided, then exit code is 3 with ambiguous input message
- [ ] Given `supertone tts "Hello" --voice v1 --output -`, then audio bytes are written to stdout and nothing else goes to stdout
- [ ] Given no `--voice` and no `default_voice` in config, then exit code is 3 with instructive message
- [ ] Given `--format json` and `--output hello.wav`, then JSON metadata with `output_file`, `duration_seconds`, `voice_id` is printed to stdout
- [ ] Given `--format json` and `--output -`, then exit code is 3 (both write to stdout)

#### Implementation Notes
- Input resolution: check `text` arg, `--input` path, `sys.stdin.isatty()`. Exactly one must be active.
- Default output: `output.<output_format>` in cwd.
- `--output -`: write to `sys.stdout.buffer`.
- Use `client.create_speech()` from ISSUE-004.
- Spinner: `output.create_progress()` on stderr if `sys.stderr.isatty()`.
- `--format json`: use `output.print_json()` with TTSResult fields.

#### Tests
- [ ] Unit: input resolution selects positional text correctly
- [ ] Unit: input resolution selects file input correctly
- [ ] Unit: input resolution detects ambiguous input (multiple sources)
- [ ] Unit: input resolution reads stdin when not TTY
- [ ] Unit: output routing writes to specified file path
- [ ] Unit: output routing writes to stdout buffer when `--output -`
- [ ] Unit: missing voice with no default raises `InputError`
- [ ] CLI test: `supertone tts "Hello" --voice v1` creates output file (mock SDK)
- [ ] CLI test: `supertone tts --input <tmpfile> --voice v1` reads file (mock SDK)
- [ ] CLI test: ambiguous input exits with code 3
- [ ] CLI test: `--format json` outputs valid JSON to stdout

#### Rollback
Revert the branch.

---

### ISSUE-006: Implement TTS voice and audio parameter flags with model validation
- Track: product
- UI: false
- Manual: false
- PRD-Ref: FR-002, US-3
- Priority: P1
- Estimate: 1d
- Status: done
- Owner:
- Branch: issue/ISSUE-006-tts-params
- GH-Issue: https://github.com/pillip/supertone-cli/issues/15
- PR: https://github.com/pillip/supertone-cli/pull/16
- Depends-On: ISSUE-005

#### Goal
All SDK audio parameters (`--speed`, `--pitch`, `--pitch-variance`, `--similarity`, `--text-guidance`, `--style`, `--include-phonemes`) are exposed as CLI flags on `supertone tts`, and model-parameter compatibility is validated before any API call.

#### Scope (In/Out)
- In: Add all parameter flags to `commands/tts.py`; model-parameter validation matrix (e.g., `--similarity` not allowed on `sona_speech_2_flash`, `--stream` only on `sona_speech_1`); pass validated params to `client.create_speech()`; `--model` enum validation
- Out: Streaming playback implementation (just the validation that `--stream` requires `sona_speech_1`), batch processing

#### Acceptance Criteria (DoD)
- [ ] Given `--model sona_speech_2_flash --similarity 0.8`, when the command runs, then exit code is 3 with message that `--similarity` is not supported by `sona_speech_2_flash`
- [ ] Given `--model sona_speech_2_flash --text-guidance 0.5`, then exit code is 3 with similar message
- [ ] Given `--stream` with `--model sona_speech_2`, then exit code is 3 with message that streaming requires `sona_speech_1`
- [ ] Given `--model invalid_model`, then exit code is 3 listing valid models
- [ ] Given `--speed 1.2 --pitch 0.5 --voice v1 "Hello"`, then both parameters are passed to `client.create_speech()`
- [ ] Given `--style calm --voice v1 "Hello"`, then the style parameter is passed to the API
- [ ] Given `--output-format flac --voice v1 "Hello"`, then the API receives flac format and output file has `.flac` extension

#### Implementation Notes
- Define a validation function `validate_params(model, **kwargs)` that checks the compatibility matrix.
- Model enum: `VALID_MODELS = {"sona_speech_1", "supertonic_api_1", "sona_speech_2", "sona_speech_2_flash"}`
- `sona_speech_2_flash` disallows: `similarity`, `text_guidance`
- `supertonic_api_1` only supports: `speed` (reject others with exit 3, per Assumption A-4)
- `--stream` only with `sona_speech_1`

#### Tests
- [ ] Unit: `validate_params("sona_speech_2_flash", similarity=0.8)` raises `InputError`
- [ ] Unit: `validate_params("sona_speech_2_flash", text_guidance=0.5)` raises `InputError`
- [ ] Unit: `validate_params("sona_speech_1", stream=True)` passes
- [ ] Unit: `validate_params("sona_speech_2", stream=True)` raises `InputError`
- [ ] Unit: `validate_params("supertonic_api_1", pitch=0.5)` raises `InputError`
- [ ] Unit: `validate_params("sona_speech_2", speed=1.2, pitch=0.5)` passes
- [ ] CLI test: invalid model name exits with code 3
- [ ] CLI test: valid params are forwarded to client (mock SDK)

#### Rollback
Revert the branch.

---

### ISSUE-007: Implement batch TTS processing (directory/glob input, progress bar)
- Track: product
- UI: true
- Manual: false
- PRD-Ref: FR-004, US-7
- Priority: P1
- Estimate: 1.5d
- Status: done
- Owner:
- Branch: issue/ISSUE-007-batch
- GH-Issue: https://github.com/pillip/supertone-cli/issues/27
- PR: https://github.com/pillip/supertone-cli/pull/28
- Depends-On: ISSUE-006

#### Goal
`supertone tts --input ./scripts/ --outdir ./audio/` processes all matching text files, shows a progress bar on TTY, handles per-file errors, and prints a summary.

#### Scope (In/Out)
- In: Batch mode detection in `commands/tts.py` (when `--input` is a directory or glob and `--outdir` is provided); file collection (top-level `.txt` for directories, glob expansion for patterns); sequential processing loop; Rich progress bar on stderr (TTY only); per-file error handling (log to stderr, continue); `--fail-fast` flag; summary line on stderr; exit code 1 if any file failed; `--outdir` creation if missing
- Out: Recursive directory traversal, concurrent processing

#### Acceptance Criteria (DoD)
- [ ] Given `--input ./scripts/ --outdir ./audio/ --voice v1`, when `./scripts/` contains `a.txt` and `b.txt`, then `./audio/a.wav` and `./audio/b.wav` are created
- [ ] Given `--input "scripts/*.txt" --outdir ./audio/ --voice v1`, then all matching files are processed
- [ ] Given `--outdir ./audio/` does not exist, then it is created before processing
- [ ] Given one file fails during batch, when `--fail-fast` is not set, then remaining files are processed and summary shows `N succeeded, M failed`
- [ ] Given `--fail-fast` and a file fails, then processing stops immediately and exit code is 1
- [ ] Given batch completes with all files succeeding, then exit code is 0
- [ ] Given batch completes with any failure, then exit code is 1
- [ ] Given stdout is a TTY, then a progress bar `X/N files` is displayed on stderr
- [ ] Given stdout is not a TTY, then the progress bar is suppressed
- [ ] Given `--input ./scripts/` and no `.txt` files exist, then exit code is 3 with descriptive message
- [ ] Given `--input "*.xyz"` matches no files, then exit code is 3

#### Implementation Notes
- Batch detection: if `--input` is a directory (`Path.is_dir()`) or contains glob chars (`*`, `?`), and `--outdir` is set.
- File collection: `Path.glob("*.txt")` for directories, `glob.glob()` for patterns.
- Output filename: `stem + "." + output_format` placed in `--outdir`.
- Progress: `output.create_progress()` wrapping the file loop.
- Use `BatchResult` and `BatchError` models from ISSUE-004.

#### Tests
- [ ] Unit: file collection from directory returns `.txt` files only
- [ ] Unit: file collection from glob pattern returns matching files
- [ ] Unit: empty directory raises `InputError`
- [ ] Unit: non-matching glob raises `InputError`
- [ ] Unit: `--outdir` is created if missing
- [ ] Unit: per-file error is captured and processing continues
- [ ] Unit: `--fail-fast` stops on first error
- [ ] CLI test: batch with 2 files creates 2 output files (mock SDK)
- [ ] CLI test: batch with 1 failure and `--fail-fast` exits 1 after first failure
- [ ] CLI test: summary line format matches `N succeeded, M failed`

#### Rollback
Revert the branch.

---

### ISSUE-008: Implement voices list command
- Track: product
- UI: true
- Manual: false
- PRD-Ref: FR-005, US-9, US-12
- Priority: P1
- Estimate: 0.5d
- Status: done
- Owner:
- Branch: issue/ISSUE-008-voices-list
- GH-Issue: https://github.com/pillip/supertone-cli/issues/11
- PR: https://github.com/pillip/supertone-cli/pull/12
- Depends-On: ISSUE-004

#### Goal
`supertone voices list` displays available voices in a table (or JSON), with optional `--type` filter for preset/custom.

#### Scope (In/Out)
- In: `commands/voices.py` — `list_voices` subcommand; `--type` filter (preset/custom); `--format` (text/json); table rendering via `output.print_table()`; JSON output via `output.print_json()`; empty result handling; register voices command group in `cli.py`
- Out: Search and clone subcommands

#### Acceptance Criteria (DoD)
- [ ] Given `supertone voices list`, when the API returns voices, then a table with Name, ID, Type, Languages columns is printed to stdout
- [ ] Given `--type preset`, then only preset voices are displayed
- [ ] Given `--type custom`, then only custom voices are displayed
- [ ] Given `--format json`, then a valid JSON array is printed to stdout with `name`, `id`, `type`, `languages` fields per object
- [ ] Given the API returns zero voices, then an empty table (with headers) or `[]` JSON is returned and exit code is 0
- [ ] Given `--type custom` with no custom voices, then a hint message is printed to stderr

#### Implementation Notes
- `commands/voices.py`: Create `voices_app = typer.Typer()`, add to main app in `cli.py`.
- `list_voices()`: call `client.list_voices()`, filter by `--type` if provided, render via `output.print_table()` or `output.print_json()`.
- Table columns: Name, ID, Type, Languages (join list with ", ").

#### Tests
- [ ] Unit: list command renders table with correct columns (mock client)
- [ ] Unit: `--type preset` filters correctly
- [ ] Unit: `--type custom` filters correctly
- [ ] Unit: `--format json` produces valid JSON array
- [ ] Unit: empty voice list returns empty table/array with exit code 0
- [ ] CLI test: `supertone voices list` exits 0 with table output (mock SDK)

#### Rollback
Revert the branch.

---

### ISSUE-009: Implement voices search command
- Track: product
- UI: true
- Manual: false
- PRD-Ref: FR-006, US-10
- Priority: P1
- Estimate: 0.5d
- Status: done
- Owner:
- Branch: issue/ISSUE-009-voices-search
- GH-Issue: https://github.com/pillip/supertone-cli/issues/17
- PR: https://github.com/pillip/supertone-cli/pull/20
- Depends-On: ISSUE-008

#### Goal
`supertone voices search` filters voices by language, gender, age, use case, and keyword, displaying results in the same table format as `voices list`.

#### Scope (In/Out)
- In: `commands/voices.py` — `search_voices` subcommand; `--lang`, `--gender`, `--age`, `--use-case`, `--query` flags; AND logic for multiple filters; `--format` (text/json); at-least-one-filter validation; empty result hint on stderr
- Out: Client-side filtering (assumes SDK/API handles filtering)

#### Acceptance Criteria (DoD)
- [ ] Given `--lang ko`, then only voices supporting Korean are returned
- [ ] Given `--gender female --lang ko`, then only voices matching both filters are returned
- [ ] Given `--query "bright"`, then voices matching the keyword are returned
- [ ] Given no filters provided, then exit code is 3 with message requiring at least one filter
- [ ] Given `--format json`, then a valid JSON array is printed
- [ ] Given no results match, then empty table is printed and a hint is shown on stderr, exit code is 0

#### Implementation Notes
- Call `client.search_voices(**filters)` passing only non-None filter values.
- If the SDK does not support server-side filtering, apply filters client-side on `list_voices()` result. Document this in code comments.
- Reuse table rendering from ISSUE-008.

#### Tests
- [ ] Unit: search with `--lang ko` passes correct filter to client (mock)
- [ ] Unit: search with multiple filters passes all (mock)
- [ ] Unit: search with no filters raises `InputError`
- [ ] Unit: empty result returns exit code 0 with hint
- [ ] CLI test: `supertone voices search --lang ko` exits 0 (mock SDK)

#### Rollback
Revert the branch.

---

### ISSUE-010: Implement TTS predict subcommand
- Track: product
- UI: false
- Manual: false
- PRD-Ref: FR-003, US-4
- Priority: P1
- Estimate: 0.5d
- Status: done
- Owner:
- Branch: issue/ISSUE-010-predict
- GH-Issue: https://github.com/pillip/supertone-cli/issues/19
- PR: https://github.com/pillip/supertone-cli/pull/22
- Depends-On: ISSUE-005

#### Goal
`supertone tts predict "text"` displays predicted audio duration and estimated credit cost without generating audio or consuming credits.

#### Scope (In/Out)
- In: `commands/tts.py` — `predict` subcommand; same input resolution as `tts` (positional, `--input`, stdin); `--voice`, `--model`, `--lang` flags; human-readable output (`Duration: 3.2s | Estimated credits: 47`); `--format json` output
- Out: Audio generation, credit deduction

#### Acceptance Criteria (DoD)
- [ ] Given `supertone tts predict "Hello" --voice v1`, then duration and credit estimate are printed to stdout in human-readable format
- [ ] Given `--input script.txt`, then file contents are used for prediction
- [ ] Given `--format json`, then output is `{"duration_seconds": ..., "estimated_credits": ...}` on stdout
- [ ] Given no audio file is created by this command
- [ ] Given the same input errors as `tts` (missing text, file not found) produce the same exit codes

#### Implementation Notes
- Reuse input resolution logic from the `tts` command (extract to a shared helper).
- Call `client.predict_duration()`.
- Human-readable format: `Duration: {d}s | Estimated credits: {c}`

#### Tests
- [ ] Unit: predict returns correct human-readable format (mock client)
- [ ] Unit: predict `--format json` returns valid JSON (mock client)
- [ ] Unit: predict with file input works (mock client)
- [ ] CLI test: `supertone tts predict "Hello" --voice v1` exits 0 (mock SDK)
- [ ] CLI test: predict does not create any files

#### Rollback
Revert the branch.

---

### ISSUE-011: Implement voices clone command
- Track: product
- UI: false
- Manual: false
- PRD-Ref: FR-007, US-11
- Priority: P1
- Estimate: 1d
- Status: done
- Owner:
- Branch: issue/ISSUE-011-voices-clone
- GH-Issue: https://github.com/pillip/supertone-cli/issues/18
- PR: https://github.com/pillip/supertone-cli/pull/21
- Depends-On: ISSUE-004

#### Goal
`supertone voices clone --name "my-narrator" --sample ./sample.wav` uploads an audio sample and returns the new voice ID.

#### Scope (In/Out)
- In: `commands/voices.py` — `clone_voice` subcommand; `--name` (required), `--sample` (required) flags; pre-upload file existence and format validation; upload progress indicator on stderr; voice_id printed to stdout; `--format json` output; supported format check
- Out: Actual API calls (tests use mocks)

#### Acceptance Criteria (DoD)
- [ ] Given `--name "my-narrator" --sample ./sample.wav`, when upload succeeds, then `voice_id` is printed to stdout and exit code is 0
- [ ] Given `--format json`, then `{"voice_id": "...", "name": "my-narrator"}` is printed to stdout
- [ ] Given `--sample ./missing.wav` (file does not exist), then exit code is 3
- [ ] Given `--sample ./sample.aac` (unsupported format), then exit code is 3 with message listing supported formats
- [ ] Given upload fails (API error), then exit code is 1 with error on stderr
- [ ] Given success, then a helpful stderr message shows how to use the new voice

#### Implementation Notes
- Supported formats: derive from SDK docs; default assumption `{wav, mp3, ogg, flac}` per UX spec.
- File extension check before upload: `Path(sample).suffix.lower()`.
- Call `client.clone_voice(name, sample_path)`.
- Print `voice_id` to stdout (for script capture), helpful message to stderr.

#### Tests
- [ ] Unit: clone with valid file calls client and prints voice_id (mock)
- [ ] Unit: clone with missing file raises `InputError`
- [ ] Unit: clone with unsupported format raises `InputError` with supported list
- [ ] Unit: `--format json` produces valid JSON
- [ ] CLI test: `supertone voices clone --name test --sample <tmpfile>` exits 0 (mock SDK)

#### Rollback
Revert the branch.

---

### ISSUE-012: Implement usage command
- Track: product
- UI: true
- Manual: false
- PRD-Ref: FR-010, US-15
- Priority: P1
- Estimate: 0.5d
- Status: done
- Owner:
- Branch: issue/ISSUE-012-usage
- GH-Issue: https://github.com/pillip/supertone-cli/issues/13
- PR: https://github.com/pillip/supertone-cli/pull/14
- Depends-On: ISSUE-004

#### Goal
`supertone usage` displays API usage (used credits, remaining credits, plan name) in human-readable or JSON format.

#### Scope (In/Out)
- In: `commands/usage.py` — `usage` command; human-readable output with Plan/Used/Remaining labels; `--format json` output; register in `cli.py`
- Out: Historical usage data, usage alerts

#### Acceptance Criteria (DoD)
- [ ] Given `supertone usage`, when the API returns usage data, then Plan, Used, and Remaining are displayed in human-readable format on stdout
- [ ] Given `--format json`, then `{"plan": "...", "used": N, "remaining": N}` is printed to stdout
- [ ] Given the API call fails, then exit code is 1 with error on stderr
- [ ] Given auth failure, then exit code is 2

#### Implementation Notes
- Call `client.get_usage()`, format via `output.py`.
- Human-readable format per UX spec: `Plan:`, `Used:`, `Remaining:` with aligned labels.

#### Tests
- [ ] Unit: usage command renders correct human-readable format (mock client)
- [ ] Unit: `--format json` produces valid JSON (mock client)
- [ ] Unit: API error results in exit code 1
- [ ] CLI test: `supertone usage` exits 0 (mock SDK)

#### Rollback
Revert the branch.

---

### ISSUE-013: Implement streaming TTS playback
- Track: product
- UI: false
- Manual: false
- PRD-Ref: FR-002 (streaming), US-3 (streaming)
- Priority: P2
- Estimate: 1d
- Status: done
- Owner:
- Branch: issue/ISSUE-013-streaming
- GH-Issue: https://github.com/pillip/supertone-cli/issues/29
- PR: https://github.com/pillip/supertone-cli/pull/30
- Depends-On: ISSUE-006

#### Goal
`supertone tts "text" --stream --model sona_speech_1` plays audio in real time via the system audio device, optionally saving to a file simultaneously.

#### Scope (In/Out)
- In: `commands/tts.py` — streaming path when `--stream` is set; `sounddevice` optional import with graceful error if not installed; real-time audio playback from `client.stream_speech()` iterator; simultaneous file save when `--output <file>` is also provided; stderr message `Streamed: X.Xs` on completion
- Out: Streaming to stdout (undefined behavior), non-`sona_speech_1` models (blocked by ISSUE-006 validation)

#### Acceptance Criteria (DoD)
- [ ] Given `--stream --model sona_speech_1 --voice v1 "Hello"`, when audio chunks arrive, then audio is played to the system output device
- [ ] Given `--stream --output file.wav --model sona_speech_1 --voice v1 "Hello"`, then audio is played AND saved to `file.wav`
- [ ] Given `--stream` and `sounddevice` is not installed, then exit code is 3 with message `pip install supertone-cli[stream]`
- [ ] Given audio device is unavailable, then exit code is 1 with descriptive error
- [ ] Given streaming completes, then stderr shows `Streamed: X.Xs`

#### Implementation Notes
- `sounddevice` import guarded by try/except `ImportError`.
- Use `sounddevice.OutputStream` to play chunks as they arrive from `client.stream_speech()`.
- If `--output` is set, tee bytes to both the audio device and a file handle.
- This is a "Could" priority in the PRD — P2 issue.

#### Tests
- [ ] Unit: streaming path calls `client.stream_speech()` (mock)
- [ ] Unit: missing `sounddevice` raises `InputError` with install message (mock ImportError)
- [ ] Unit: audio device error raises `CLIError` (mock sounddevice)
- [ ] Unit: simultaneous file save writes all chunks to file (mock)
- [ ] CLI test: `--stream` without sounddevice installed exits 3

#### Rollback
Revert the branch.

---

### ISSUE-014: Optimize startup latency with lazy imports and add CI benchmark
- Track: platform
- UI: false
- Manual: false
- PRD-Ref: NFR-002
- Priority: P1
- Estimate: 0.5d
- Status: done
- Owner:
- Branch: issue/ISSUE-014-lazy-imports
- GH-Issue: https://github.com/pillip/supertone-cli/issues/23
- PR: https://github.com/pillip/supertone-cli/pull/24
- Depends-On: ISSUE-005

#### Goal
`supertone --help` completes in under 500ms, verified by an automated benchmark test.

#### Scope (In/Out)
- In: Audit and fix all imports in `cli.py` to ensure command modules, SDK, and Rich are lazy-loaded; add a pytest benchmark test that measures `supertone --help` wall-clock time; ensure `supertone` SDK is only imported inside `client.py` function bodies
- Out: General performance optimization of API calls

#### Acceptance Criteria (DoD)
- [ ] Given all dependencies are installed, when `time supertone --help` is run 10 times, then the median wall-clock time is < 500ms
- [ ] Given `cli.py`, when inspected, then no command module is imported at module level (all are lazy via Typer callback pattern or deferred import)
- [ ] Given `client.py`, when inspected, then `import supertone` appears only inside function bodies, not at module level
- [ ] Given a benchmark test exists, when `uv run pytest tests/test_startup.py` is run, then the test asserts startup time < 500ms

#### Implementation Notes
- In `cli.py`, use Typer's lazy group loading. Register command groups with callbacks, import command modules inside the callback.
- Check that `rich` is not imported at module level in `cli.py`.
- Benchmark test: use `subprocess.run(["supertone", "--help"])` and measure `time.perf_counter()` delta.

#### Tests
- [ ] Benchmark: `supertone --help` subprocess completes in < 500ms (10-run median)
- [ ] Static: grep `cli.py` for module-level imports of `commands`, `supertone`, `rich` — assert none

#### Rollback
Revert the branch.

---

### ISSUE-015: Set up CI pipeline (GitHub Actions)
- Track: platform
- UI: false
- Manual: false
- PRD-Ref: NFR-004
- Priority: P1
- Estimate: 0.5d
- Status: done
- Owner:
- Branch: issue/ISSUE-015-ci
- GH-Issue: https://github.com/pillip/supertone-cli/issues/25
- PR: https://github.com/pillip/supertone-cli/pull/26
- Depends-On: ISSUE-005

#### Goal
A GitHub Actions CI pipeline runs lint, tests, and coverage checks on every push and PR, enforcing the >80% coverage target.

#### Scope (In/Out)
- In: `.github/workflows/ci.yml` — matrix (Python 3.11, 3.12, 3.13 on ubuntu-latest and macos-latest); steps: `uv sync`, `uv run ruff check .`, `uv run pytest --cov=src --cov-report=term-missing`, coverage threshold assertion; startup benchmark step
- Out: PyPI publish workflow (Phase 1 does not require automated publishing), CD

#### Acceptance Criteria (DoD)
- [ ] Given a push to `main` or a PR, when CI runs, then all tests pass on Python 3.11, 3.12, 3.13
- [ ] Given CI runs, when coverage is below 80%, then the pipeline fails
- [ ] Given CI runs, when `ruff check .` finds issues, then the pipeline fails
- [ ] Given CI runs, then `supertone --help` startup benchmark step executes and logs the time

#### Implementation Notes
- Use `astral-sh/setup-uv` action for uv installation.
- Coverage enforcement: `uv run pytest --cov=src --cov-report=term-missing --cov-fail-under=80`
- Matrix: `{os: [ubuntu-latest, macos-latest], python: [3.11, 3.12, 3.13]}`

#### Tests
- [ ] CI workflow YAML is valid (lintable)
- [ ] CI passes locally with `act` or manual workflow dispatch

#### Rollback
Delete the workflow file.

---

### ISSUE-016: Declare supertone SDK as a required dependency in pyproject.toml
- Track: platform
- UI: false
- Manual: false
- PRD-Ref: NFR-001
- Priority: P0
- Estimate: 0.5d
- Status: done
- Owner:
- Branch: issue/ISSUE-016-declare-sdk-dependency
- GH-Issue: https://github.com/pillip/supertone-cli/issues/32
- PR:
- Depends-On: none

#### Goal
`pip install supertone-cli` in a clean environment results in a working CLI. Currently `src/supertone_cli/client.py` imports `from supertone import Supertone` but `pyproject.toml` does not list `supertone` in `[project].dependencies`. A fresh install will crash with `ImportError` on the first command.

#### Scope (In/Out)
- In: Add `"supertone>=0.2,<0.3"` to `[project].dependencies` in `pyproject.toml`; run `uv sync` to regenerate `uv.lock` with `supertone` locked; verify `uv run supertone --help` works in the project venv (not system Python); add an optional `# SDK version` comment if helpful
- Out: SDK-side changes; major-version upgrades beyond 0.2.x

#### Acceptance Criteria (DoD)
- [ ] Given a fresh checkout, when `uv sync` is run, then `supertone` 0.2.x appears in `uv.lock` and in the installed packages of the project venv
- [ ] Given a fresh virtualenv and `pip install .`, when `supertone --help` is executed, then it exits 0 without `ImportError`
- [ ] Given `pyproject.toml`, when inspected, then `[project].dependencies` contains an entry for `supertone` with a version constraint of `>=0.2,<0.3`
- [ ] Given the existing test suite, when `uv run pytest -q` is run, then all tests still pass

#### Implementation Notes
- Current installed SDK version: 0.2.0. Use range `>=0.2,<0.3` to guard against breaking 0.3.x changes while allowing minor patches.
- File to edit: `pyproject.toml` `[project].dependencies` array.
- The `# type: ignore[import-untyped]` comment at `src/supertone_cli/client.py:51` may be removable if the SDK ships a `py.typed` marker — check and remove if redundant, otherwise leave it.
- Do NOT move this dep into an optional extra; the CLI is non-functional without it.
- After editing `pyproject.toml`, run `uv sync` and commit the updated `uv.lock`.

#### Tests
- [ ] Existing test suite (`uv run pytest -q`) still passes after the dependency is declared
- [ ] Regression smoke: `python -c "import supertone_cli.client"` succeeds in a fresh venv created from `pip install .`

#### Rollback
Revert the `pyproject.toml` change and run `uv sync` to restore the previous `uv.lock`.

---

### ISSUE-017: Rewrite README with installation, auth, and usage examples
- Track: platform
- UI: false
- Manual: false
- PRD-Ref: NFR-001
- Priority: P0
- Estimate: 1d
- Status: done
- Owner:
- Branch: issue/ISSUE-017-readme-rewrite
- GH-Issue: https://github.com/pillip/supertone-cli/issues/32
- PR:
- Depends-On: none

#### Goal
A public user landing on the PyPI page or GitHub repo has enough information to install, authenticate, and run a first successful TTS request within ~2 minutes. The current `README.md` is 4 lines and omits every essential section.

#### Scope (In/Out)
- In: Rewrite `README.md` to include: short tagline; feature bullets (tts / voices / usage / config / streaming / batch); installation (`pip install supertone-cli` + optional `[stream]` extra); authentication (`SUPERTONE_API_KEY` env var OR `supertone config set api_key <key>`); quickstart examples for `supertone tts`, `supertone voices list/search`, `supertone tts-predict`, `supertone usage balance`, piping (stdin/stdout/output redirection), batch mode, streaming mode; exit codes table (0 success, 1 general/API, 2 auth, 3 input); link to CHANGELOG and LICENSE; CI badge
- Out: Full API reference (users can run `--help`); contributor guide; architecture deep-dive

#### Acceptance Criteria (DoD)
- [ ] Given a new user reads `README.md`, when they follow the Installation section verbatim, then they end up with a working `supertone --help` command without needing any additional steps
- [ ] Given `README.md`, when inspected, then it contains all of the following sections: Features, Installation, Authentication, Quickstart, Examples, Exit Codes, License
- [ ] Given the Quickstart section, when each `supertone tts` command snippet is cross-referenced with `src/supertone_cli/commands/tts.py`, then all flags used in the snippet are valid flags on the current CLI
- [ ] Given the Exit Codes section, when compared with `src/supertone_cli/errors.py`, then codes 0, 1, 2, and 3 are documented and match the implementation

#### Implementation Notes
- Write in English (primary) for PyPI discoverability. Korean translation is out of scope.
- Reference env var override precedence: CLI flags > env vars > config file > defaults (matches `src/supertone_cli/config.py` behavior).
- Verify every example by cross-referencing `src/supertone_cli/commands/tts.py`, `src/supertone_cli/commands/voices.py`, `src/supertone_cli/commands/usage.py` — do not document flags that do not exist.
- If the README exceeds ~250 lines, move deep examples to `docs/examples.md` and link from the README.
- CI badge URL pattern: `https://github.com/pillip/supertone-cli/actions/workflows/ci.yml/badge.svg`

#### Tests
- [ ] Manual: copy each code block in the README into a shell (with a valid API key) and confirm it exits 0
- [ ] Cross-reference: for each CLI flag mentioned in README examples, confirm the flag exists in the relevant `commands/*.py` file

#### Rollback
Revert `README.md` to the previous 4-line version.

---

### ISSUE-018: Add MIT LICENSE file to repository root
- Track: platform
- UI: false
- Manual: false
- PRD-Ref: NFR-001
- Priority: P0
- Estimate: 0.5d
- Status: done
- Owner:
- Branch: issue/ISSUE-018-add-license-file
- GH-Issue: https://github.com/pillip/supertone-cli/issues/32
- PR:
- Depends-On: none

#### Goal
`pyproject.toml` declares `license = { text = "MIT" }` but no `LICENSE` file exists in the repo root. This causes PyPI warnings, prevents GitHub from showing a license badge, and leaves legal status ambiguous for downstream users.

#### Scope (In/Out)
- In: Create `LICENSE` file at repo root containing the standard MIT license text with `Copyright (c) 2026 pillip youn`; ensure `pyproject.toml` `license` field remains consistent (update to `license = { file = "LICENSE" }` if SPDX table form is preferred, otherwise keep `text = "MIT"`)
- Out: CLA, NOTICE file, third-party license aggregation

#### Acceptance Criteria (DoD)
- [ ] Given the repo root, when `ls` is run, then a file named exactly `LICENSE` exists
- [ ] Given `LICENSE` is opened, when read, then it contains the standard MIT license text with copyright year 2026 and holder `pillip youn`
- [ ] Given `uv build` is run, when the produced wheel is inspected, then `LICENSE` is included in the distribution
- [ ] Given a GitHub view of the repo, when the repository page is rendered, then the license badge shows "MIT"

#### Implementation Notes
- Use the canonical OSI MIT template (https://opensource.org/license/mit) — plain text only, no hyperlinks inside the file.
- If switching `pyproject.toml` to `license = { file = "LICENSE" }`, verify the build succeeds with hatchling before committing; otherwise keep `text = "MIT"` and simply add the file alongside it.
- The LICENSE file must be at the repo root (not in `src/` or `docs/`).

#### Tests
- [ ] Manual: run `uv build` and inspect `dist/*.whl` contents to confirm `LICENSE` is present (e.g., `unzip -l dist/*.whl | grep LICENSE`)

#### Rollback
Delete the `LICENSE` file. If `pyproject.toml` was modified, revert that change as well.

---

### ISSUE-019: Clean up repo artifacts and strengthen .gitignore
- Track: platform
- UI: false
- Manual: false
- PRD-Ref: NFR-001
- Priority: P0
- Estimate: 1d
- Status: done
- Owner:
- Branch: issue/ISSUE-019-repo-cleanup
- GH-Issue: https://github.com/pillip/supertone-cli/issues/32
- PR:
- Depends-On: none

#### Goal
The repo currently ships development and runtime artifacts that should not be public. Remove them from git tracking, update `.gitignore` to prevent re-entry, and configure hatchling to exclude registry and tooling files from the published sdist/wheel.

#### Scope (In/Out)
- In: `git rm` the following tracked artifacts: `demo.wav`, `pipe.wav`, `voice_sample.wav`, `.DS_Store`, `audio/` directory, `scripts/scene1.txt`, `scripts/scene2.txt`, `scripts/scene3.txt`, `docs/sprint_state.md`, `docs/review_notes.md`, `docs/ui_review_notes.md`; update `.gitignore` to include `*.wav`, `*.mp3`, `.DS_Store`, `audio/`, `dist/`, `build/`, `*.egg-info/`, `.coverage`, `htmlcov/`, `.venv/`, `.worktrees/`, `.pytest_cache/`, `.ruff_cache/`; add hatchling `exclude` patterns in `pyproject.toml` so `issues.md`, `STATUS.md`, `.claude/`, `.claude-kit/`, and `audio/` are excluded from the published sdist/wheel
- Out: Removing `issues.md` or `STATUS.md` from the repo (they stay on main but are excluded from the package); altering `.claude/` or `.claude-kit/` directory contents; removing legitimate source code or tests

#### Acceptance Criteria (DoD)
- [ ] Given `git ls-files`, when inspected, then none of `demo.wav`, `pipe.wav`, `voice_sample.wav`, `.DS_Store`, `audio/*`, `scripts/scene1.txt`, `scripts/scene2.txt`, `scripts/scene3.txt`, `docs/sprint_state.md`, `docs/review_notes.md`, `docs/ui_review_notes.md` appear as tracked files
- [ ] Given `.gitignore`, when inspected, then it contains entries for `*.wav`, `.DS_Store`, `audio/`, `.venv/`, `dist/`, `build/`, `*.egg-info/`, `.coverage`, `htmlcov/`, `.pytest_cache/`, and `.ruff_cache/`
- [ ] Given `uv build` is run and the sdist is inspected, when `tar tzf dist/supertone_cli-*.tar.gz` is run, then `issues.md`, `STATUS.md`, `docs/sprint_state.md`, and `.claude*/` paths are absent from the archive
- [ ] Given `uv run pytest -q` is run after the cleanup, when all tests complete, then the full test suite still passes

#### Implementation Notes
- Before deleting audio files, search `tests/` with Grep for any reference to `voice_sample.wav`, `demo.wav`, or `pipe.wav`. If a test depends on a sample file, move a small stub into `tests/fixtures/` rather than deleting it.
- Use `git rm --cached <file>` for files to stop tracking without deleting locally; use `git rm <file>` for hard-delete of files that are not needed at all.
- Configure hatchling exclusions in `pyproject.toml`:
  ```toml
  [tool.hatch.build.targets.sdist]
  exclude = ["issues.md", "STATUS.md", "docs/sprint_state.md", "docs/review_notes.md", "docs/ui_review_notes.md", ".claude/", ".claude-kit/", ".worktrees/", "audio/", "*.wav"]
  [tool.hatch.build.targets.wheel]
  # already scoped to packages = ["src/supertone_cli"] — no additional exclude needed
  ```
- Do NOT touch `PRD.md` — that is project-defining content.
- `STATUS.md` and `issues.md` are registry files; they remain in the repo but must not appear in the published package.

#### Tests
- [ ] Given `uv run pytest -q` after cleanup, when all tests run, then the suite is green with no test referencing a deleted file
- [ ] Given `uv build && tar tzf dist/supertone_cli-*.tar.gz | grep -E 'issues.md|STATUS.md|\.wav|\.DS_Store'`, when run, then the command produces no output

#### Rollback
Run `git restore` to recover deleted files from the previous commit if needed.

---

### ISSUE-020: Enrich pyproject.toml metadata (author, urls, classifiers, keywords)
- Track: platform
- UI: false
- Manual: false
- PRD-Ref: NFR-001
- Priority: P0
- Estimate: 0.5d
- Status: done
- Owner:
- Branch: issue/ISSUE-020-pyproject-metadata
- GH-Issue: https://github.com/pillip/supertone-cli/issues/32
- PR:
- Depends-On: none

#### Goal
Make the PyPI page informative and searchable. The current `pyproject.toml` has minimal metadata — no author email, no project URLs, no classifiers, and no keywords. A public release requires all four to be present for discoverability and PyPI validation.

#### Scope (In/Out)
- In: Update `[project]` in `pyproject.toml` with: `authors` (name + email), expanded `description` (1-line public-facing), `keywords`, `classifiers` (Development Status, Intended Audience, License, OS, Python versions, Topic, Environment); add `[project.urls]` table with `Homepage`, `Repository`, `Issues`, `Changelog` pointing at the GitHub repo
- Out: Changing the package version; third-party badges in README (that is ISSUE-017); CHANGELOG file creation

#### Acceptance Criteria (DoD)
- [ ] Given `pyproject.toml`, when inspected, then `[project].authors` contains `{ name = "pillip youn", email = "pillip@supertone.ai" }` and `[project].keywords` and `[project].classifiers` are non-empty lists
- [ ] Given `pyproject.toml`, when inspected, then `[project.urls]` contains at minimum `Homepage`, `Repository`, `Issues`, and `Changelog` keys pointing at `https://github.com/pillip/supertone-cli` paths
- [ ] Given `uv build` is run and the wheel metadata is inspected with `unzip -p dist/*.whl '*/METADATA'`, when the output is reviewed, then Author-email, Home-page, Project-URL, Keyword, and Classifier fields all appear
- [ ] Given `twine check dist/*`, when run after `uv build`, then no warnings or errors are reported
- [ ] Given `uv run pytest -q`, when run after the metadata change, then all tests still pass

#### Implementation Notes
- Do NOT change the version field — version bumps are a separate release concern.
- Classifier strings must be exact Trove strings from https://pypi.org/classifiers/. Suggested classifiers:
  ```toml
  classifiers = [
      "Development Status :: 4 - Beta",
      "Environment :: Console",
      "Intended Audience :: Developers",
      "Intended Audience :: End Users/Desktop",
      "License :: OSI Approved :: MIT License",
      "Operating System :: OS Independent",
      "Programming Language :: Python :: 3",
      "Programming Language :: Python :: 3.11",
      "Programming Language :: Python :: 3.12",
      "Programming Language :: Python :: 3.13",
      "Topic :: Multimedia :: Sound/Audio :: Speech",
      "Topic :: Software Development :: Libraries :: Python Modules",
  ]
  ```
- Suggested keywords: `["tts", "text-to-speech", "supertone", "cli", "speech-synthesis", "voice-cloning", "audio"]`
- If a CHANGELOG file does not yet exist, point the `Changelog` URL at the GitHub releases page (`https://github.com/pillip/supertone-cli/releases`).
- Install `twine` via `uv add twine --dev` if not already present to run `twine check`.

#### Tests
- [ ] Given `uv build && twine check dist/*`, when run, then the command exits 0 with no warnings
- [ ] Given `uv run pytest -q`, when run after the metadata change, then all existing tests still pass

#### Rollback
Revert `pyproject.toml` to the previous state.

---

### ISSUE-021: Add CHANGELOG.md for 0.1.0 release
- Track: platform
- UI: false
- Manual: false
- PRD-Ref: NFR-001
- Priority: P1
- Estimate: 0.5d
- Status: done
- Owner:
- Branch: issue/ISSUE-021-changelog
- GH-Issue: https://github.com/pillip/supertone-cli/issues/32
- PR: https://github.com/pillip/supertone-cli/pull/44
- Depends-On: none

#### Goal
A `CHANGELOG.md` exists at the repo root following Keep a Changelog 1.1.0 format, documenting the 0.1.0 initial release so users can see what has shipped without reading commit history.

#### Scope (In/Out)
- In: Create `CHANGELOG.md` at the repo root following `https://keepachangelog.com/en/1.1.0/` conventions. Include an `## [Unreleased]` section and a `## [0.1.0] - 2026-04-11` section covering: initial public release with `tts`, `tts-predict`, `voices {list,search,get,clone,edit,delete}`, `usage {balance,analytics,voices}`, `config {init,set,get,list}`; features (streaming via `--stream`, batch via `--outdir`, JSON output, Unix pipe support, NO_COLOR, exit code conventions); platform (Python 3.12+, MIT license). Link releases at the bottom with GitHub compare URLs. Add `[project.urls].Changelog` in `pyproject.toml` pointing at the GitHub releases page or direct `CHANGELOG.md` link.
- Out: Historical reconstruction of internal issue-level changes; auto-generated changelog tooling (e.g., git-cliff, release-please) — Phase 1 uses hand-curated entries.

#### Acceptance Criteria (DoD)
- [ ] Given the repo root, when listed, then `CHANGELOG.md` exists.
- [ ] Given `CHANGELOG.md`, when inspected, then it contains a header matching Keep a Changelog format and a `## [0.1.0] - 2026-04-11` section with Added/Fixed/Changed subsections as appropriate.
- [ ] Given `CHANGELOG.md`, when inspected, then it lists every top-level CLI command (`tts`, `tts-predict`, `voices`, `usage`, `config`) under Added.
- [ ] Given `pyproject.toml`, when inspected, then the `[project.urls].Changelog` key is present and its URL is valid (repo releases page or direct CHANGELOG.md link).

#### Implementation Notes
- Use the canonical Keep a Changelog 1.1.0 format. Section order: Added, Changed, Deprecated, Removed, Fixed, Security (omit empty sections).
- Keep entries user-facing. Internal refactors and tests belong in the commit history, not the changelog.
- Link format at the bottom: `[0.1.0]: https://github.com/pillip/supertone-cli/releases/tag/v0.1.0`
- File to create: `CHANGELOG.md` at repo root. File to update: `pyproject.toml` `[project.urls]` table (from ISSUE-020).

#### Tests
- [ ] Manual: open in a markdown renderer and verify formatting renders correctly with no broken links.

#### Rollback
Delete the `CHANGELOG.md` file and revert the `pyproject.toml` URL addition.

---

### ISSUE-022: Replace `_is_auth_error` string heuristic with typed SDK exceptions
- Track: product
- UI: false
- Manual: false
- PRD-Ref: FR-009, NFR-005
- Priority: P2
- Estimate: 0.5d
- Status: done
- Owner:
- Branch: issue/ISSUE-022-typed-auth-errors
- GH-Issue: https://github.com/pillip/supertone-cli/issues/32
- PR: https://github.com/pillip/supertone-cli/pull/47
- Depends-On: none

#### Goal
`client.py` stops detecting authentication errors by inspecting the exception message string. Instead it catches the specific `supertone` SDK exception class (if one exists) or checks a documented HTTP status attribute, so auth errors are classified correctly even when the SDK message wording changes.

#### Scope (In/Out)
- In: Investigate what exception types `supertone>=0.2,<0.3` raises for 401/403 responses (inspect `.venv/lib/python3.12/site-packages/supertone/` for `errors.py`, `exceptions.py`, or a base error class). Replace `_is_auth_error(exc)` in `src/supertone_cli/client.py` (currently the heuristic around lines 30–35) with either: (a) an `isinstance()` check against the SDK's dedicated auth exception class, or (b) a check on the HTTP status code attribute if the SDK exposes a response object on the exception. Fall back to the existing string match only if the SDK offers neither. Apply the same replacement to every call site that currently uses `_is_auth_error`.
- Out: Re-classifying other error categories (rate limits, server errors) — this issue is scoped strictly to auth.

#### Acceptance Criteria (DoD)
- [ ] Given the SDK raises its auth exception (or a 401-bearing exception), when the `client.py` error-translation path catches it, then `AuthError` is raised with exit code 2.
- [ ] Given the SDK raises a non-auth exception (e.g., 500) whose message happens to contain the word "auth", when caught, then `APIError` is raised with exit code 1 (not misclassified as auth).
- [ ] Given the existing test suite, when `uv run pytest -q` is run, then all tests pass without modification to test files.
- [ ] Given `client.py`, when grep'd for `_is_auth_error`, then the function either no longer exists or is annotated as a last-resort fallback with a comment explaining why.

#### Implementation Notes
- Start by inspecting `.venv/lib/python3.12/site-packages/supertone/` to discover the exception hierarchy. Look for `errors.py`, `exceptions.py`, or a base error class in `__init__.py`.
- Add a new unit test in `tests/test_client.py` that raises the real SDK exception type and asserts `AuthError` is produced.
- Add a second unit test that raises a non-auth exception with "auth" literally in its message and asserts `APIError` is produced (regression guard against the old heuristic).
- If the SDK has no typed exceptions, document that in a comment above the heuristic and include a reference to an upstream issue (if one can be filed).

#### Tests
- [ ] Unit: mock SDK raises its auth exception type → our wrapper surfaces `AuthError` with exit code 2.
- [ ] Unit: mock SDK raises a non-auth exception whose message contains "auth" → our wrapper surfaces `APIError` with exit code 1.

#### Rollback
Revert the commit. The string heuristic is restored.

---

### ISSUE-023: Extract repeated `hasattr` boilerplate in client.py into a helper
- Track: product
- UI: false
- Manual: false
- PRD-Ref: NFR-004
- Priority: P2
- Estimate: 0.5d
- Status: done
- Owner:
- Branch: issue/ISSUE-023-client-attr-helper
- GH-Issue: https://github.com/pillip/supertone-cli/issues/32
- PR: https://github.com/pillip/supertone-cli/pull/48
- Depends-On: none

#### Goal
`client.py` contains roughly 40 lines of repetitive `v.attr if hasattr(v, "attr") else default` patterns when converting SDK response objects to internal dataclasses (`Voice`, `Usage`, `Prediction`). Extract this into a small private helper so each conversion site becomes a single line and future SDK field changes touch one place.

#### Scope (In/Out)
- In: Add a private helper (e.g., `_attr(obj, name, default=None)`) in `src/supertone_cli/client.py` that returns `getattr(obj, name, default)` with explicit handling for the list-wrapping behavior needed by the `languages` field. Replace all duplicated `hasattr`-ternary patterns in `list_voices`, `list_custom_voices`, `search_voices`, `get_voice`, `get_usage`, `get_usage_analytics`, and `get_voice_usage`. Preserve exact current semantics including the `language` → `[language]` list-wrapping fallback.
- Out: Changing the `Voice`, `Usage`, or `Prediction` dataclass field shapes; adding new fields; changing the SDK-response contract; extracting to a separate module.

#### Acceptance Criteria (DoD)
- [ ] Given `list_voices()` is called with a mock SDK response, when compared against pre-refactor expectations, then the returned `Voice` objects are identical to the pre-refactor output.
- [ ] Given `client.py`, when grep'd for `hasattr(v,`, then the match count drops by at least 20 (ideally to zero in conversion paths).
- [ ] Given the full test suite, when `uv run pytest -q` is run, then all 106 tests pass with no modifications to test files.

#### Implementation Notes
- `getattr(obj, "attr", default)` is equivalent to the hasattr-ternary in every current usage. The only subtle case is list-wrapping for `language` (if the SDK returns a single string, wrap it in a list); this needs a dedicated helper or inline handling adjacent to `_attr`.
- Do NOT introduce Pydantic, dataclass inheritance, or any new abstraction beyond the one helper function.
- Keep the helper private (`_`-prefix) and file-local to `client.py`. Do not export it from the module.
- The existing tests in `tests/test_client.py` already cover all conversion paths; no new tests are required unless behavior changes (it should not).

#### Tests
- [ ] Run existing `uv run pytest -q` — all 106 tests must pass unchanged as the sole verification of correct refactor behavior.

#### Rollback
Revert the commit. No persistent state is created.

---

### ISSUE-024: Track upstream SDK fix for `list_custom_voices` raw HTTP fallback
- Track: product
- UI: false
- Manual: false
- PRD-Ref: FR-005
- Priority: P2
- Estimate: 0.5d
- Status: done
- Owner:
- Branch: issue/ISSUE-024-track-custom-voices-sdk-bug
- GH-Issue: https://github.com/pillip/supertone-cli/issues/32
- PR: https://github.com/pillip/supertone-cli/pull/46
- Depends-On: none

#### Goal
`client.list_custom_voices()` currently bypasses the `supertone` SDK and calls the REST API directly via `httpx` because the SDK's Pydantic model for custom voice responses requires a `description` field that the live API does not return. This workaround is fragile (bypasses the SDK's auth, retry, and observability). Add a tracking mechanism so the fallback can be deleted cleanly when upstream ships a fix.

#### Scope (In/Out)
- In: (1) Confirm the bug still reproduces against `supertone==0.2.0` with a minimal repro snippet. (2) File an issue on the upstream `supertone` SDK repository (or create `docs/upstream_bugs.md` if no public tracker exists) describing the bug: API does not return `description`, but the SDK Pydantic model requires it. (3) Add a comment block above `list_custom_voices` in `src/supertone_cli/client.py` linking to the upstream issue URL and the SDK version at which it was observed. (4) Add a `# TODO(ISSUE-024)` marker so the workaround is discoverable when upgrading the SDK.
- Out: Fixing the upstream SDK; removing the workaround (that happens when upstream ships a fix); changing runtime behavior in any way.

#### Acceptance Criteria (DoD)
- [ ] Given `src/supertone_cli/client.py:list_custom_voices`, when inspected, then a comment block documents the upstream bug, the SDK version it was observed against (`supertone==0.2.0`), and a link to the upstream issue or `docs/upstream_bugs.md`.
- [ ] Given the repo, when grep'd for `TODO(ISSUE-024)`, then at least one marker exists near the raw HTTP workaround code.
- [ ] Given the upstream issue (once filed) or `docs/upstream_bugs.md`, when inspected, then it includes a minimal repro snippet and the SDK version.

#### Implementation Notes
- Do NOT change runtime behavior — the `httpx` workaround stays until upstream ships a fix.
- If no public bug tracker exists for the SDK (it may be internal), record the bug in `docs/upstream_bugs.md` and link to that file from the `client.py` comment. The intent is traceability, not a specific platform.
- The comment block should follow the pattern: `# WORKAROUND(ISSUE-024): <description>. See: <link>. Remove when supertone>0.2.x fixes the Pydantic model.`

#### Tests
- [ ] None — this is a documentation-only change. The existing test suite (`uv run pytest -q`) must still pass unchanged.

#### Rollback
Revert the comment block and delete `docs/upstream_bugs.md` if it was created.

---

### ISSUE-025: Add optional E2E smoke test behind `-m integration` mark
- Track: platform
- UI: false
- Manual: false
- PRD-Ref: NFR-004
- Priority: P2
- Estimate: 1d
- Status: done
- Owner:
- Branch: issue/ISSUE-025-integration-smoke-test
- GH-Issue: https://github.com/pillip/supertone-cli/issues/32
- PR: https://github.com/pillip/supertone-cli/pull/49
- Depends-On: none

#### Goal
A single end-to-end smoke test exists that exercises the real `supertone` SDK against the live API when `SUPERTONE_API_KEY` is set, gated behind pytest marker `integration` so it never runs in the default `uv run pytest -q` invocation. This gives developers and releasers a one-command sanity check before cutting a release.

#### Scope (In/Out)
- In: Register `integration` as a named pytest marker in `pyproject.toml` `[tool.pytest.ini_options].markers`. Add `tests/integration/test_smoke.py` with a single test `test_voices_list_smoke` that invokes `supertone voices list --format json` via `typer.testing.CliRunner`, asserts exit code 0, and asserts the JSON output contains at least one preset voice. Decorate the test with both `@pytest.mark.integration` and `@pytest.mark.skipif(not os.environ.get("SUPERTONE_API_KEY"), reason="needs API key")`. Add `tests/integration/__init__.py`. Add a `tests/integration/README.md` explaining how to run `uv run pytest -m integration`.
- Out: VCR/cassette fixtures (v0 uses live API); integration tests for destructive commands (`voices clone`, `voices delete`); CI-scheduled nightly runs (separate infra issue).

#### Acceptance Criteria (DoD)
- [ ] Given `uv run pytest -q` is run without `SUPERTONE_API_KEY` set, when the suite completes, then the integration test is skipped and all 106 unit tests pass.
- [ ] Given `uv run pytest -m integration` is run with a valid `SUPERTONE_API_KEY`, when the test completes, then `test_voices_list_smoke` passes with exit code 0.
- [ ] Given `pyproject.toml`, when inspected, then `[tool.pytest.ini_options].markers` includes an entry for `integration` describing that it marks tests hitting the real Supertone API.
- [ ] Given `tests/integration/test_smoke.py`, when opened, then the test uses both `pytest.mark.integration` and `pytest.mark.skipif` keyed on `SUPERTONE_API_KEY`.

#### Implementation Notes
- Use `typer.testing.CliRunner` to invoke the CLI; assert via `result.exit_code` and `json.loads(result.stdout)`.
- The smoke test must be strictly read-only (`voices list`) — never call destructive endpoints.
- Do NOT add the integration test to the default CI job in `.github/workflows/ci.yml`. It runs only when a developer explicitly opts in.
- If `[tool.pytest.ini_options]` already has `filterwarnings`, `addopts`, or other keys in `pyproject.toml`, preserve them — only append the `markers` key.

#### Tests
- [ ] Given `uv run pytest -q` without `SUPERTONE_API_KEY`, when the suite runs, then the integration test appears as skipped (s) and 106 unit tests pass.
- [ ] Given `uv run pytest -m integration` with `SUPERTONE_API_KEY` set, when the test runs, then it exits 0.

#### Rollback
Delete `tests/integration/` and remove the `integration` marker entry from `pyproject.toml`.

---

### ISSUE-026: Remove repo-root ruff.toml symlink, consolidate lint config in pyproject.toml
- Track: platform
- UI: false
- Manual: false
- PRD-Ref: NFR-004
- Priority: P1
- Estimate: 0.5d
- Status: done
- Owner:
- Branch: issue/ISSUE-026-consolidate-ruff-config
- GH-Issue: https://github.com/pillip/supertone-cli/issues/32
- PR: https://github.com/pillip/supertone-cli/pull/45
- Depends-On: none

#### Goal
`uv run ruff check .` produces a clean result locally. Currently a `ruff.toml` symlink at the repo root points into `.claude-kit/linters/`, silently overriding the `[tool.ruff]` section in `pyproject.toml`, using stricter settings (line-length 88 vs 100), and causing ruff to scan the entire `.claude-kit/` submodule and report 200+ phantom errors from files that are not part of the project. This issue removes the symlink and makes `pyproject.toml` the single source of lint config.

#### Scope (In/Out)
- In: Delete the `ruff.toml` symlink at the repo root (`rm ruff.toml` — safe because it is a symlink, not a real file). Add `extend-exclude = [".claude-kit", ".claude", ".venv", ".worktrees", "dist", "build"]` to the `[tool.ruff]` section in `pyproject.toml`. Run `uv run ruff check .` and confirm it exits 0 or reports issues only in `src/` and `tests/`. Auto-fix any real lint issues found in project source with `--fix` or manual edits; do not silence by lowering strictness.
- Out: Reconciling the dev-kit submodule's linting philosophy; changing line-length to 88; modifying `.claude-kit/` contents.

#### Acceptance Criteria (DoD)
- [ ] Given the repo root, when listed, then no file or symlink named `ruff.toml` exists.
- [ ] Given `uv run ruff check .`, when executed, then the command exits 0 with no errors reported from `.claude-kit/` or `.venv/`.
- [ ] Given `pyproject.toml`, when inspected, then `[tool.ruff].extend-exclude` includes at minimum `.claude-kit` and `.venv`.
- [ ] Given `pyproject.toml`, when inspected, then it is the sole source of ruff configuration (no external `ruff.toml` at the repo root or any parent directory within the project).

#### Implementation Notes
- The `ruff.toml` symlink currently targets `.claude-kit/linters/ruff.toml`, which specifies `line-length = 88`, `target-version = "py311"`, `[lint] select = ["E", "F", "I"]`. Our `pyproject.toml` already has `line-length = 100`, `target-version = "py312"`, `[lint] select = ["E", "F", "I", "W"]` — our settings are stricter and more current. No migration from the submodule config is needed.
- Command to remove the symlink: `rm /Users/pillip/project/supertone-cli/ruff.toml` (it is a symlink — safe to `rm`).
- After adding `extend-exclude`, run `uv run ruff check src tests` to verify 0 errors. If any genuine errors surface in project source, fix them rather than suppressing them.
- Verify the full test suite still passes after any lint-driven code fixes: `uv run pytest -q`.

#### Tests
- [ ] Given `uv run ruff check .`, when run after the symlink removal and `extend-exclude` addition, then the command exits 0.
- [ ] Given `uv run pytest -q`, when run after any lint-driven code fixes, then all tests pass.

#### Rollback
Re-create the symlink with `ln -s .claude-kit/linters/ruff.toml ruff.toml` and revert the `pyproject.toml` `extend-exclude` addition.

---

### ISSUE-027: Wire up SDK-wide CLI surface (voice settings, voices CRUD, usage subcommands)
- Track: product
- UI: true
- Manual: false
- PRD-Ref: FR-002, FR-005, FR-010
- Priority: P1
- Estimate: 1d
- Status: done
- Owner:
- Branch: issue/ISSUE-027-sdk-wide-surface
- GH-Issue: https://github.com/pillip/supertone-cli/issues/32
- PR: https://github.com/pillip/supertone-cli/pull/31
- Depends-On: none

#### Goal
Expose the full SDK feature surface in the CLI: TTS voice/audio parameter flags (--style/--speed/--pitch/--pitch-variance/--similarity/--text-guidance), voices get/edit/delete, and usage balance/analytics/voices subcommand group.

#### Scope (In/Out)
- In: TTS voice settings CLI flags + model validation, voices get/edit/delete subcommands, usage subcommand group refactor, Voice.languages default, 26 new tests (10 client wrapper + 16 command-level).
- Out: CHANGELOG, integration tests, auth heuristic, hasattr cleanup.

#### Acceptance Criteria (DoD)
- [x] Given `supertone voices --help`, then get/clone/edit/delete are listed.
- [x] Given `supertone usage --help`, then balance/analytics/voices are listed.
- [x] Given voice setting flags, then create_speech receives the correct kwargs.
- [x] Given `uv run pytest -q`, then 131 tests pass.
- [x] Given `uv run pytest --cov=src --cov-fail-under=80`, then coverage >= 80%.
- [x] CI: 4/4 pass (ubuntu/macos × 3.12/3.13).

#### Tests
- [x] 131 passed (106 baseline + 16 command + 10 client wrapper - 1 reclassified).

#### Rollback
Revert the squash-merge commit on main.

---

### ISSUE-028: Remove list_custom_voices httpx workaround once SDK makes description optional
- Track: quality
- UI: false
- Manual: false
- PRD-Ref: FR-005
- Priority: P2
- Estimate: 0.5d
- Status: done
- Owner:
- Branch: issue/ISSUE-028-remove-custom-voices-httpx-workaround
- GH-Issue: https://github.com/supertone-inc/supertone-cli/issues/51
- PR: https://github.com/supertone-inc/supertone-cli/pull/52
- Depends-On: ISSUE-024; upstream supertone SDK release with description optional in custom voice Pydantic model

#### Goal
Once the upstream `supertone` SDK ships a release that makes the `description` field optional in the custom voice Pydantic response model (resolving the bug tracked by ISSUE-024 and `docs/upstream_bugs.md`), remove the raw httpx workaround in `src/supertone_cli/client.py:list_custom_voices` and revert to using the SDK call. Clean up the workaround tracking artifacts (test, doc, comment marker). The CLI's user-facing surface — including `supertone voices edit --description` — already treats description as optional and requires no changes.

#### Scope (In/Out)
- In: (1) Replace the raw `httpx.get(...)` workaround in `src/supertone_cli/client.py:list_custom_voices` (currently lines ~317-354) with `client.custom_voices.list_custom_voices()` SDK call. Map response items to `Voice(...)` using existing `_attr` helper. (2) Remove the `WORKAROUND(ISSUE-024)` comment block above `list_custom_voices`. (3) Remove (or fully rewrite) `tests/test_upstream_bugs.py` — the assertions about `WORKAROUND(ISSUE-024)` marker and `0.2` SDK version no longer hold. (4) Mark `docs/upstream_bugs.md` "list_custom_voices" entry as **Resolved** with the fixed SDK version, or remove the section entirely if it leaves the doc empty. (5) Bump the `supertone` minimum version constraint in `pyproject.toml` to the version that includes the fix.
- Out: Changing CLI command flags, output shape, or user-facing behavior (none required — already optional). Other unrelated SDK upgrade work. Filing the upstream fix itself (handled by the SDK team).

#### Acceptance Criteria (DoD)
- [ ] Given `src/supertone_cli/client.py:list_custom_voices`, when inspected, then it calls `client.custom_voices.list_custom_voices()` (no `httpx` import or call inside the function) and the `WORKAROUND(ISSUE-024)` comment block is removed.
- [ ] Given the repo, when grep'd for `WORKAROUND(ISSUE-024)` or `TODO(ISSUE-024)`, then no matches remain.
- [ ] Given `tests/test_upstream_bugs.py`, when inspected, then it either no longer exists or no longer asserts the workaround marker / SDK 0.2 version.
- [ ] Given `docs/upstream_bugs.md`, when inspected, then the `list_custom_voices` entry's Status is `Resolved` (with the fixing SDK version) or the section is removed.
- [ ] Given `pyproject.toml`, when inspected, then the `supertone` dependency's minimum version pins the fixed release.
- [ ] Given `uv run pytest -q`, when run, then all tests pass with the workaround removed.
- [ ] Given `supertone voices list-custom` (manual smoke against live API or integration mark), when run, then output matches the prior httpx-based behavior.

#### Implementation Notes
- **Do not start until** the upstream `supertone` SDK ships a release where the custom voice Pydantic model makes `description` optional (or the API guarantees `description` is always returned). Verify with a 2-line repro before kicking off: `from supertone import Supertone; Supertone(api_key=...).custom_voices.list_custom_voices()` should not raise `pydantic.ValidationError`.
- The CLI command layer (`src/supertone_cli/commands/voices.py`) and `edit_custom_voice` already treat description as optional (`Optional[str] = None`), so no changes there.
- After SDK call replacement, ensure exception mapping (`AuthError`/`APIError`) still works; the existing `try/except` structure should be reused.
- Update `tests/test_voices.py` only if existing assertions break (they shouldn't — `description=None` mock assertion is unaffected by request-side optional-ness).

#### Tests
- [ ] Unit: `tests/test_client.py` — adjust or add a test that mocks `client.custom_voices.list_custom_voices()` returning items without a `description` field, asserting `Voice(...)` is built correctly.
- [ ] Existing `tests/test_upstream_bugs.py` removed or fully rewritten — must not assert workaround markers.
- [ ] `uv run pytest -q` passes.

#### Rollback
Revert the commit. The httpx workaround returns; pin the `supertone` version back if it was bumped.

---


## Self-Review Summary

### Requirement Coverage
| Requirement | Issue(s) |
|-------------|----------|
| FR-001 (TTS input/output) | ISSUE-005 |
| FR-002 (voice/audio params) | ISSUE-006 |
| FR-003 (TTS predict) | ISSUE-010 |
| FR-004 (batch processing) | ISSUE-007 |
| FR-005 (voices list) | ISSUE-008 |
| FR-006 (voices search) | ISSUE-009 |
| FR-007 (voices clone) | ISSUE-011 |
| FR-008 (config) | ISSUE-003 |
| FR-009 (output/error) | ISSUE-002 |
| FR-010 (usage) | ISSUE-012 |
| NFR-001 (installability) | ISSUE-001 |
| NFR-002 (startup latency) | ISSUE-014 |
| NFR-003 (API key security) | ISSUE-003 |
| NFR-004 (test coverage) | ISSUE-015 |
| NFR-005 (exit codes) | ISSUE-002 |
| US-1 (single TTS) | ISSUE-005 |
| US-2 (file input) | ISSUE-005 |
| US-3 (params) | ISSUE-006 |
| US-3 streaming | ISSUE-013 |
| US-4 (predict) | ISSUE-010 |
| US-5 (piped input) | ISSUE-005 |
| US-6 (stdout output) | ISSUE-005 |
| US-7 (batch) | ISSUE-007 |
| US-8 (JSON output) | ISSUE-005, ISSUE-008, ISSUE-009, ISSUE-010, ISSUE-011, ISSUE-012 |
| US-9 (list voices) | ISSUE-008 |
| US-10 (search voices) | ISSUE-009 |
| US-11 (clone voice) | ISSUE-011 |
| US-12 (preset vs custom) | ISSUE-008 |
| US-13 (API key setup) | ISSUE-003 |
| US-14 (default settings) | ISSUE-003 |
| US-15 (usage) | ISSUE-012 |

**Orphaned requirements**: None.

### Dependency Graph Validation
- Critical path: 001 -> 002 -> 003 -> 004 -> 005 -> 006 -> 007 (7 steps)
- No circular dependencies.
- Parallel tracks after ISSUE-004: voices (008, 009, 011), usage (012), predict (010 after 005).

### Sizing Re-check
- All issues are 0.5d to 1.5d. No issue exceeds 1.5d.
- ISSUE-003 (config, 1.5d) and ISSUE-005 (single TTS, 1.5d) are at the upper bound but each is a cohesive unit that cannot be split without creating dependencies between halves.
- ISSUE-007 (batch, 1.5d) is complex but self-contained.

### AC Testability
- All AC items use Given/When/Then format.
- Each can be directly translated to a test case.

### Confidence Rating
**High**. All FRs, NFRs, and user stories are covered. Architecture is detailed and module boundaries are clear. The only uncertainty is the exact Supertone SDK API surface, mitigated by the client wrapper pattern in ISSUE-004.

### Manual Setup Tasks
No external service provisioning is needed for implementation. The Supertone API key is a user-provided credential, not a platform provisioning task. All tests use mocked SDK calls. No manual setup issues are required.
