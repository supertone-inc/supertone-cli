"""E2E smoke tests gated on SUPERTONE_API_KEY.

These tests hit the real Supertone API and are excluded from the default
test suite.  Run explicitly with:

    uv run pytest -m integration

They require a valid SUPERTONE_API_KEY environment variable.
"""

import json
import os

import pytest
from typer.testing import CliRunner

from supertone_cli.cli import app

runner = CliRunner()

_HAS_KEY = bool(os.environ.get("SUPERTONE_API_KEY"))


@pytest.mark.integration
@pytest.mark.skipif(not _HAS_KEY, reason="SUPERTONE_API_KEY not set")
def test_voices_list_smoke():
    """Smoke test: voices list returns valid JSON with at least one voice."""
    result = runner.invoke(app, ["voices", "list", "--format", "json"])
    assert result.exit_code == 0, f"CLI failed: {result.output}"
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) > 0, "Expected at least one voice from the API"
    # Verify basic voice structure
    voice = data[0]
    assert "id" in voice
    assert "name" in voice
