# Review Notes — ISSUE-028

## Code Review
- **Verdict**: Approve with nits.
- The diff cleanly removes the `WORKAROUND(ISSUE-024)` block in `src/supertone_cli/client.py:list_custom_voices` and restores the SDK call via `client.custom_voices.list_custom_voices()`, mapped through the existing `_attr` / `_build_voice` helpers — consistent with `list_voices` / `search_voices` / `get_voice`.
- Exception mapping (`AuthError` / `APIError`) reuses the standard `try/except` chain. `pydantic.ValidationError` from a future SDK regression would be surfaced as `APIError` via the existing `Exception` fallback — acceptable.
- `pyproject.toml` floor bumped to `supertone>=0.2.1,<0.3`. `uv.lock` regen drops transitive `numpy` / `sounddevice` (upstream dropped them). In scope.
- Tests pass: 152 passed, 1 skipped (`integration` marker, requires API key). Ruff clean.

### Behavior change worth noting
- `voices list-custom --format json` may now include `languages`, `gender`, `age`, `use_cases` keys when the SDK returns them. The prior httpx path emitted only `id`, `name`, `type`. Additive; consistent with preset listings. Captured in `CHANGELOG.md` `[Unreleased]`.

### Cosmetic
- Three unrelated line-wraps at `client.py:110-112`, `:147-149`, `:163-165` from the local 88-char `ruff.toml` symlink. Out-of-scope reformat; not a blocker (ruff is clean).
- `test_list_custom_voices_does_not_use_httpx` (test_client.py) and `test_list_custom_voices_no_longer_uses_httpx` (test_upstream_bugs.py) overlap. Acceptable belt-and-suspenders for a one-time regression guard; consider deleting one after a release cycle.

## Security Findings
- **None observed.** Removing the manual `x-sup-api-key` header injection slightly *reduces* surface — the SDK manages auth internally via `Supertone(api_key=...)`. No new sinks. Existing API-key sanitizer in the error layer continues to apply.
- Dependency hygiene: `supertone==0.2.1` upgrade is upstream-driven and net-positive (smaller install footprint, fewer transitive CVE surfaces).

## AC Coverage

| AC | Evidence |
|---|---|
| `list_custom_voices` calls SDK; no httpx; no marker | `src/supertone_cli/client.py:323-335` |
| Repo grep for `WORKAROUND(ISSUE-024)` / `TODO(ISSUE-024)` returns no production matches | grep clean (only inside intentional regression-guard test strings) |
| `tests/test_upstream_bugs.py` no longer asserts marker / `0.2` | rewritten as regression guard |
| `docs/upstream_bugs.md` entry marked Resolved with fixing version | `docs/upstream_bugs.md` Status line |
| `pyproject.toml` pins fixed release | `pyproject.toml:35` |
| `uv run pytest -q` passes | 152 passed, 1 skipped |
| Manual smoke matches prior behavior | Owner-verified path; not run in this review |

## Fixes Applied During Review
- Added `[Unreleased]` section to `CHANGELOG.md` (managed on main via `flock_edit.sh`) capturing the SDK floor bump and the JSON output widening.

## Follow-ups
- After 1–2 releases, drop one of the duplicate "no httpx in `list_custom_voices`" source-inspection tests.
- Consider a project policy: cosmetic reformat-only hunks land in their own commit, not mixed with logic changes.

## ISSUE-029 — usage analytics ISO datetime

Bug-fix PR adding `_to_iso_datetime(value, *, end)` in `src/supertone_cli/client.py`
and applying it to `start_time`/`end_time` in `get_usage_analytics` only.

### Verdict: APPROVE

Scope is minimal and matches the issue exactly. `get_voice_usage` is untouched
(0 references in the client diff). The lazy `supertone` import inside
`get_usage_analytics` is preserved; `_to_iso_datetime` is a pure string helper
that imports nothing, so startup latency (NFR-002) is unaffected.

### Code Review findings

- AC met: date-only start -> `...T00:00:00Z`; date-only end -> `...T23:59:59Z`;
  a value already containing `T` is passed through unchanged. Confirmed by
  `client.py:472-482, 497-498`.
- Tests assert SDK kwargs via a mocked `client.usage.get_usage` (start-of-day,
  end-of-day, and pass-through cases) and a CLI test exits 0. Test code reviewed
  with the same rigor; the mock shape (`data` -> bucket -> `results`) matches what
  `get_usage_analytics` parses, so the green is meaningful, not a false positive.
- [Low] Lowercase `t` detection gap: the membership test `"T" in value` only
  matches uppercase `T`. ISO-8601 permits a lowercase `t` separator. A value like
  `2026-06-01t08:30:00Z` would be mis-treated as date-only and mangled into
  `...t08:30:00ZT00:00:00Z`. Not exploitable and not produced by the documented
  `YYYY-MM-DD` CLI input; left as-is to avoid gold-plating. Fix if ever needed:
  `if "T" in value or "t" in value`.
- [Low] No validation of empty/malformed input: `""` becomes `"T00:00:00Z"` and
  would yield a server 400. This is no worse than pre-fix behavior and no upstream
  validation existed; out of scope for this PR.
- [Info] The `Z` (UTC) assumption is hardcoded. Acceptable: the CLI documents
  plain `YYYY-MM-DD` and the endpoint accepts UTC; documenting timezone behavior
  in `--help` would be a nice future touch, not a blocker.

### Security Findings

- No new secrets, credentials, or API keys introduced.
- No injection surface: helper does pure string concatenation of values that are
  later sent as SDK kwargs over HTTPS (no shell, no SQL, no template).
- Error handling unchanged: existing `AuthError`/`APIError` mapping in
  `get_usage_analytics` is preserved; the helper raises nothing new.
- No XSS / deserialization / CORS surface (CLI, no web output).
- Overall: no security findings at any severity.

### Self-review

- Severity re-assessment: only two Low findings; neither has an exploit path or
  data-loss path, so Low is justified (not politics).
- False-positive check: verified the pass-through branch and mock shape against
  the real parsing code; confirmed `get_voice_usage` diff is empty.
- Blind-spot scan: re-read for injection/secrets/error-handling/auth — none apply
  to a pure string helper on a CLI.
- AC verification: all three transformation rules + `get_voice_usage` untouched +
  test expectations are satisfied.
- Confidence: High.

### Tests / Lint

- `uv run pytest -q`: 157 passed, 1 skipped.
- `uv run ruff check .`: All checks passed.

### Fixes applied during review

None. No Critical/High findings; the Low items are intentionally not gold-plated.

### Follow-ups (non-blocking)

- Optional: accept lowercase `t` separator and/or validate input format in the
  CLI layer for clearer error messages than a server 400.
