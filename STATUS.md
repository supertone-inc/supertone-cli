# STATUS — Supertone CLI

**Last updated**: 2026-06-17
**Current milestone**: Phase 1 — SDK 래퍼 CLI

---

## Issue Summary

| 구분 | 수량 |
|------|------|
| **Total** | 31 |
| P0 (Must) | 10 |
| P1 (Should) | 14 |
| P2 (Could) | 7 |

### By Track

| Track | Issues | Est. |
|-------|--------|------|
| Foundation | ISSUE-001, 002 | 1.5d |
| Config | ISSUE-003 | 1.5d |
| Client | ISSUE-004 | 1d |
| TTS | ISSUE-005, 006, 007, 010, 013 | 5.5d |
| Voices | ISSUE-008, 009, 011 | 2d |
| Usage | ISSUE-012 | 0.5d |
| Product (post-MVP) | ISSUE-027, 030 | 1.5d |
| Platform | ISSUE-014, 015, 016, 017, 018, 019, 020, 021, 025, 026 | 5.5d |
| Quality | ISSUE-022, 023, 024, 028, 029 | 2.5d |

**Total estimate**: ~22d

---

## Key Risks

| Risk | Severity | Status |
|------|----------|--------|
| SDK API surface changes | High | Mitigated by client.py wrapper |
| Streaming needs audio lib (sounddevice) | Medium | Resolved — optional extra `[stream]` |
| API beta instability | Medium | Integration tests separated |
| Test coverage for interactive/streaming | Medium | Dependency injection for mocking |

---

## Next Issues to Implement

1. ~~**ISSUE-029** (P1, bug) — Fix `usage analytics` date serialization~~ — shipped (PR #56)
2. ~~**ISSUE-030** (P1, bug) — Fix `voices get` 404 on cloned/custom voices~~ — shipped (PR #58)
3. ~~**ISSUE-031** (P1, bug) — Fix `--stream` default model — auto-select `sona_speech_1` when no `-m`~~ — shipped (PR #60)

### Prior Backlog

1. **ISSUE-016** (P0) — Declare supertone SDK as a required dependency in pyproject.toml
2. **ISSUE-018** (P0) — Add MIT LICENSE file to repository root
3. **ISSUE-020** (P0) — Enrich pyproject.toml metadata (author, urls, classifiers, keywords)
4. **ISSUE-019** (P0) — Clean up repo artifacts and strengthen .gitignore
5. **ISSUE-017** (P0) — Rewrite README with installation, auth, and usage examples

### Post-Release Polish

1. **ISSUE-021** (P1) — Add CHANGELOG.md for 0.1.0 release
2. **ISSUE-026** (P1) — Remove repo-root ruff.toml symlink, consolidate lint config in pyproject.toml
3. **ISSUE-022** (P2) — Replace `_is_auth_error` string heuristic with typed SDK exceptions
4. **ISSUE-023** (P2) — Extract repeated `hasattr` boilerplate in client.py into a helper
5. **ISSUE-024** (P2) — Track upstream SDK fix for `list_custom_voices` raw HTTP fallback
6. **ISSUE-025** (P2) — Add optional E2E smoke test behind `-m integration` mark

---

## Warnings

**Issue Validation** (76 violations, non-blocking):
- **AC format**: 65 acceptance criteria are not in strict Given/When/Then format. Content is clear and testable; format is a style preference.
- **Dependency depth**: 11 issues have chain depth > 3. This is expected — the foundation chain (scaffold → errors → config → client → commands) is 4-6 deep by design.

These are informational only and do not block implementation.

---

## Documents

| Document | Status |
|----------|--------|
| PRD | v1.1 Complete |
| Requirements | v1.0 Complete |
| UX Spec | v1.0 Complete |
| Architecture | v1.0 Complete |
| Data Model | v1.0 Complete |
| Test Plan | v1.0 Complete |
| Issues | 31 issues created |
