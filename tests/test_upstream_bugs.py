"""Regression guard for ISSUE-024 / ISSUE-028 — workaround removed."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_workaround_marker_removed_from_client():
    """No WORKAROUND(ISSUE-024) or TODO(ISSUE-024) markers remain in client.py."""
    content = (ROOT / "src" / "supertone_cli" / "client.py").read_text()
    assert "WORKAROUND(ISSUE-024)" not in content
    assert "TODO(ISSUE-024)" not in content


def test_list_custom_voices_no_longer_uses_httpx():
    """list_custom_voices source must not import or call httpx."""
    import inspect

    from supertone_cli.client import list_custom_voices

    src = inspect.getsource(list_custom_voices)
    assert "httpx" not in src


def test_upstream_bugs_doc_marks_resolved_or_removed():
    """docs/upstream_bugs.md either omits the entry or marks it Resolved."""
    upstream = ROOT / "docs" / "upstream_bugs.md"
    if not upstream.exists():
        return
    content = upstream.read_text()
    if "list_custom_voices" in content:
        assert "Resolved" in content, (
            "if list_custom_voices entry remains, it must be marked Resolved"
        )
