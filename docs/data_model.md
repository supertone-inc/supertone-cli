# Data Model

## Storage Strategy

- **Primary storage**: Local filesystem -- single TOML config file at `~/.config/supertone/config.toml`.
- **Choice rationale**: The CLI is a stateless, single-invocation tool. The only persistent state is user configuration (API key, defaults). TOML is specified by the PRD, `tomllib` is stdlib in Python 3.11+, and `tomli_w` is a zero-dependency write companion. No database, no cache, no search index.
- **Secondary storage**: None. All non-config data (voices, usage, predictions) is transient -- fetched from the Supertone API per invocation and discarded after the process exits.
- **File permissions**: Config file is set to `0o600` (owner read/write only) on every write operation (NFR-003).

---

## Access Patterns

Since there is no database, "access patterns" describes how each command reads/writes the config file and what API response structures it consumes.

| Pattern | Source (Command) | Operation | Data Touched | Frequency |
|---------|-----------------|-----------|--------------|-----------|
| Resolve API key | All authenticated commands | Read config + env var | `api_key` field | Every invocation |
| Resolve defaults | `tts`, `tts predict` | Read config | `default_voice`, `default_model`, `default_lang` | Every TTS invocation |
| Config init | `config init` | Write config (full) | All 4 config keys | Once per setup |
| Config set | `config set` | Read-modify-write config | Single key | Low frequency |
| Config get | `config get` | Read config | Single key | Low frequency |
| Config list | `config list` | Read config | All keys | Low frequency |
| List voices | `voices list` | API read | List of Voice objects | Medium |
| Search voices | `voices search` | API read | Filtered list of Voice objects | Medium |
| Clone voice | `voices clone` | API write (upload) | CloneResult object | Low |
| TTS generate | `tts` | API write (generate) | Audio bytes + TTS metadata | High |
| TTS predict | `tts predict` | API read | Prediction object | Medium |
| Check usage | `usage` | API read | Usage object | Low |

---

## Schema

### Config File: `~/.config/supertone/config.toml`

This is the only persistent data structure. It is a flat TOML file with no sections (Phase 1).

| Key | Type | Required | Default | Validation | Description |
|-----|------|----------|---------|------------|-------------|
| `api_key` | string | No (but needed for auth commands) | None | Non-empty string; must not be whitespace-only | Supertone API key |
| `default_voice` | string | No | None | Non-empty string if present | Default voice ID for TTS commands |
| `default_model` | string | No | `"sona_speech_2"` (built-in fallback) | One of: `sona_speech_1`, `supertonic_api_1`, `supertonic_api_3`, `sona_speech_2`, `sona_speech_2_flash`, `sona_speech_2t` | Default TTS model |
| `default_lang` | string | No | `"ko"` (built-in fallback) | Non-empty string if present | Default language code |

**Constraints**:
- File permissions: `0o600` enforced on every write.
- Valid settable keys: Only the 4 keys above are accepted by `config set`. Unknown keys are rejected with exit code 3.
- Empty values: `config set api_key ""` is rejected (exit code 3). Other keys accept empty string to clear the default.

**Example file**:
```toml
api_key = "sk-abc123def456"
default_voice = "voice-id-123"
default_model = "sona_speech_2"
default_lang = "ko"
```

**Resolution order** (highest priority wins):
1. CLI flags (`--voice`, `--model`, `--lang`)
2. Environment variables (`SUPERTONE_API_KEY` for api_key only)
3. Config file values
4. Built-in defaults (`model=sona_speech_2`, `lang=ko`, `format=wav`)

---

### API Response Model: Voice

Returned by `client.list_voices()` and `client.search_voices()`. Not persisted.

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `id` | `str` | No | Unique voice identifier |
| `name` | `str` | No | Human-readable voice name |
| `type` | `str` (enum: `"preset"` / `"custom"`) | No | Voice origin type |
| `languages` | `list[str]` | No (may be empty list) | Supported language codes |
| `gender` | `str` | Yes | Voice gender descriptor |
| `age` | `str` | Yes | Voice age descriptor |
| `use_cases` | `list[str]` | No (may be empty list) | Applicable use case tags |

**Validation rules**:
- `id` and `name` must be non-empty strings.
- `type` must be one of `"preset"` or `"custom"`.
- `languages` and `use_cases` must be lists (empty is acceptable).
- `gender` and `age` may be `None` or absent in the API response; the CLI treats missing values as empty string for display.

**Python representation** (used in `client.py` and `output.py`):

```python
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Voice:
    id: str
    name: str
    type: str  # "preset" | "custom"
    languages: list[str] = field(default_factory=list)
    gender: str = ""
    age: str = ""
    use_cases: list[str] = field(default_factory=list)
```

---

### API Response Model: Usage

Returned by `client.get_usage()`. Not persisted.

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `used` | `int` | No | Credits consumed in current period |
| `remaining` | `int` | No | Credits remaining |
| `plan` | `str` | No | Plan name (e.g., "Pro", "Free") |

**Validation rules**:
- `used` and `remaining` must be non-negative integers.
- `plan` must be a non-empty string.

**Python representation**:

```python
@dataclass(frozen=True)
class Usage:
    used: int
    remaining: int
    plan: str
```

---

### API Response Model: Prediction

Returned by `client.predict_duration()`. Not persisted.

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `duration_seconds` | `float` | No | Predicted audio duration in seconds |
| `estimated_credits` | `int` | No | Estimated credit cost |

**Validation rules**:
- `duration_seconds` must be a non-negative number.
- `estimated_credits` must be a non-negative integer.

**Python representation**:

```python
@dataclass(frozen=True)
class Prediction:
    duration_seconds: float
    estimated_credits: int
```

---

### API Response Model: CloneResult

Returned by `client.clone_voice()`. Not persisted.

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `voice_id` | `str` | No | Newly registered voice ID |
| `name` | `str` | No | Voice name as registered |

**Validation rules**:
- Both fields must be non-empty strings.

**Python representation**:

```python
@dataclass(frozen=True)
class CloneResult:
    voice_id: str
    name: str
```

---

### API Response Model: TTSResult

Metadata returned alongside audio generation (used for `--format json` and stderr summary). Not persisted.

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `output_file` | `str` | Yes (stdout mode) | Path to written audio file |
| `duration_seconds` | `float` | No | Audio duration in seconds |
| `voice_id` | `str` | No | Voice used for generation |
| `characters_processed` | `int` | No | Number of characters processed |

**Python representation**:

```python
@dataclass(frozen=True)
class TTSResult:
    output_file: str | None
    duration_seconds: float
    voice_id: str
    characters_processed: int
```

---

### Internal Model: BatchResult

Aggregated result of batch processing. Used by `commands/tts.py` and `output.py`. Not persisted.

| Field | Type | Description |
|-------|------|-------------|
| `succeeded` | `int` | Count of successfully processed files |
| `failed` | `int` | Count of failed files |
| `results` | `list[TTSResult]` | Individual results for successful files |
| `errors` | `list[BatchError]` | Individual errors for failed files |

```python
@dataclass
class BatchError:
    file_path: str
    error_message: str


@dataclass
class BatchResult:
    succeeded: int = 0
    failed: int = 0
    results: list[TTSResult] = field(default_factory=list)
    errors: list[BatchError] = field(default_factory=list)
```

---

### Internal Model: Resolved Config

The merged configuration after applying resolution order. Used internally by `config.py` and consumed by command modules. Never written to disk in this form.

| Field | Type | Source |
|-------|------|--------|
| `api_key` | `str | None` | env var > config file > None |
| `default_voice` | `str | None` | config file > None |
| `default_model` | `str` | config file > `"sona_speech_2"` |
| `default_lang` | `str` | config file > `"ko"` |

This is not a separate class; it is the `dict` returned by `load_config()` with env var overrides applied.

---

### Error Hierarchy

Defined in `errors.py`. These are not data models in the traditional sense, but they carry structured data (message + exit code) through the CLI.

| Exception | Exit Code | Trigger |
|-----------|-----------|---------|
| `CLIError` | 1 | Base class; general failures |
| `AuthError` | 2 | Missing or invalid API key |
| `InputError` | 3 | Bad arguments, missing required options, incompatible params |
| `APIError` | 1 | API request failures (network, rate limit, server error) |

---

## Enumerations

These are fixed value sets used across multiple modules.

### Model Names

```python
VALID_MODELS = {
    "sona_speech_1",
    "supertonic_api_1",
    "supertonic_api_3",
    "sona_speech_2",
    "sona_speech_2_flash",
    "sona_speech_2t",
}
```

Used for validation in `commands/tts.py` and `config set default_model`.

### Audio Output Formats

```python
VALID_OUTPUT_FORMATS = {"wav", "mp3", "ogg", "flac", "aiff"}
```

Used for `--output-format` validation.

### Voice Types

```python
VALID_VOICE_TYPES = {"preset", "custom"}
```

Used for `--type` filter in `voices list`.

### Config Keys

```python
VALID_CONFIG_KEYS = {"api_key", "default_voice", "default_model", "default_lang"}
```

Used for validation in `config set` and `config get`.

---

## Constraints and Validation

### Config File (Filesystem-Level)

| Constraint | Enforcement |
|------------|-------------|
| File permissions `0o600` | Set by `save_config()` after every write via `os.chmod()` |
| Parent directory created if missing | `config.py` creates `~/.config/supertone/` with `mkdir(parents=True)` |
| Only valid keys accepted | `config set` rejects unknown keys with exit code 3 |
| `api_key` non-empty | `config set api_key ""` rejected; `config init` repeats prompt |
| `default_model` value range | Must be in `VALID_MODELS` if set |

### Application-Level Validation (Command Modules)

| Rule | Location | Exit Code |
|------|----------|-----------|
| Exactly one input source (text arg, `--input`, stdin) | `commands/tts.py` | 3 |
| `--similarity` and `--text-guidance` rejected for `sona_speech_2_flash` | `commands/tts.py` | 3 |
| `--stream` only with `sona_speech_1` | `commands/tts.py` | 3 |
| `--format json` with `--output -` is ambiguous | `commands/tts.py` | 3 |
| `--input` file must exist and be non-empty | `commands/tts.py` | 3 |
| `--sample` file must exist and have supported format | `commands/voices.py` | 3 |
| Batch mode requires `--outdir` | `commands/tts.py` | 3 |
| At least one filter for `voices search` | `commands/voices.py` | 3 |
| API key must be present for authenticated commands | `client.py` | 2 |
| API key never appears in error output | `errors.py` (strips key from messages) | N/A |

---

## Config File Migration Strategy

### Phase 1

No `version` key. The config file is a flat key-value TOML with 4 known keys. No migration logic needed.

### Phase 2 (Forward-Looking)

When the config schema needs to change (e.g., adding `[profiles]` sections, new keys):

1. **Add a `version` key**: New config files are written with `version = 2` at the top.
2. **Migrate on read**: `load_config()` checks for the `version` key:
   - If absent (Phase 1 file): apply migration function `_migrate_v1_to_v2()` which restructures the flat keys into the new format and writes back with `version = 2`.
   - If `version = 2`: read normally.
3. **Migration function is idempotent**: Running it on an already-migrated file produces the same result.
4. **Backup before migration**: Before any migration write, copy the original file to `config.toml.bak`.

**Example Phase 2 config structure** (speculative):

```toml
version = 2
api_key = "sk-..."

[defaults]
voice = "voice-id-123"
model = "sona_speech_2"
lang = "ko"

[profiles.narrator]
voice = "voice-id-456"
model = "sona_speech_1"
lang = "en"
style = "calm"
```

The migration function would move `default_voice` -> `defaults.voice`, `default_model` -> `defaults.model`, etc.

---

## Data Flow Diagrams

### Config Read Flow

```
CLI flag --voice? -----> Use flag value
        |
        v (no flag)
Env var SUPERTONE_API_KEY? ---> Use env var (api_key only)
        |
        v (no env var)
Read ~/.config/supertone/config.toml
        |
        v (key present?)
        Yes -> Use config value
        No  -> Use built-in default (model/lang) or None (voice/api_key)
```

### TTS Command Data Flow

```
Input Resolution          Parameter Resolution         API Call              Output
-----------------         --------------------         --------              ------
TEXT arg  ─┐              --voice / config ─┐          client.create_speech  Audio bytes -> file
--input   ─┼─> text ───> --model / config ─┼─> params ──────────────────> TTSResult -> stderr
stdin     ─┘              --lang  / config ─┘                              JSON -> stdout (if --format json)
```

### Batch Processing Data Flow

```
--input dir/glob ──> resolve file list ──> for each file:
                                              read text
                                              client.create_speech(text, params)
                                              write output file
                                              update BatchResult
                                           ──> print summary to stderr
```

---

## Serialization

### Config File (TOML)

- **Read**: `tomllib.load()` (stdlib, Python 3.11+). Returns `dict[str, str]`.
- **Write**: `tomli_w.dump()`. Accepts `dict[str, str]`.
- **Round-trip**: No comment or formatting preservation needed (machine-managed file). `tomli_w` produces clean TOML.

### JSON Output (`--format json`)

- **Serialization**: `json.dumps()` on dataclass-to-dict conversion via `dataclasses.asdict()`.
- **Output target**: stdout only.
- All JSON output must be valid, parseable JSON. No trailing commas, no comments.

### Audio Output

- Raw bytes from the SDK. Written to file via `Path.write_bytes()` or streamed to stdout via `sys.stdout.buffer.write()`.
- No serialization/deserialization by the CLI; the SDK handles audio encoding.

---

## Scaling Notes

This section addresses how the data model holds up as usage grows.

### Current Design Handles

- Single user, single config file, sequential API calls.
- Batch sizes of ~100 files (limited by sequential processing and API rate limits).
- Voice lists of ~1000 entries (rendered in a single table; no pagination needed).

### At 10x (Phase 2 Additions)

- **Multiple profiles**: Add `[profiles.<name>]` TOML sections. Config migration strategy is defined above.
- **Concurrent batch processing**: `BatchResult` model already supports aggregation; adding `ThreadPoolExecutor` does not change the data model.
- **Larger voice lists**: If API paginates, `client.py` iterates pages transparently. The `Voice` model does not change.

### At 100x

- **Not expected for a CLI tool**. If this becomes a service, the entire architecture changes (database, queue, etc.) and this data model is no longer applicable.
- The only risk is batch files exceeding memory when loading all text into memory at once. Mitigation: stream file contents per-file (already the design -- each file is read and processed individually).

---

## Self-Review

### Access Pattern Coverage

Every command from the UX spec has a corresponding access pattern in the table above. Verified:
- `tts` / `tts predict` -> Resolve API key, Resolve defaults, TTS generate / TTS predict
- `voices list` / `search` / `clone` -> Resolve API key, List/Search/Clone voices
- `usage` -> Resolve API key, Check usage
- `config init` / `set` / `get` / `list` -> Config init / set / get / list

No uncovered access patterns.

### Constraint Audit

- `api_key`: NOT NULL enforced at `config set` (rejects empty). Nullable at read (absence is valid, triggers exit code 2 at use time).
- `default_model`: Validated against `VALID_MODELS` enum at `config set`.
- `default_voice` and `default_lang`: Validated as non-empty strings if provided, but allowed to be absent.
- All API response fields: Non-nullable fields documented; nullable fields (`gender`, `age`) explicitly marked.

### N+1 / Performance Check

Not applicable -- there is no database. Each command makes at most 1 API call (batch makes N sequential calls, one per file, which is inherent to the task).

Config file is read once per invocation via `load_config()`. No repeated reads.

### Confidence Rating

**High**. The data model is minimal and well-defined:
- The config file schema is explicitly specified in the PRD and architecture document.
- API response models are documented in the architecture.
- There are no ambiguous relationships, no complex joins, no caching concerns.
- The only uncertainty is the exact SDK response shape, which is mitigated by the `client.py` wrapper that normalizes responses into the documented dataclasses.
