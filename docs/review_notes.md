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
