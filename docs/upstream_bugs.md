# Upstream SDK Bugs

Tracking known bugs in the `supertone` SDK that require workarounds in `supertone-cli`.

---

## list_custom_voices Pydantic ValidationError

- **SDK Version**: supertone==0.2.0
- **Observed**: 2026-04-03
- **Status**: Resolved in supertone==0.2.1 (2026-05-10) — workaround removed in ISSUE-028
- **Tracker**: ISSUE-024 (resolved by ISSUE-028)

### Description

The SDK's `custom_voices.list_custom_voices()` method fails with a Pydantic `ValidationError` because the response model requires a `description` field that the live API (`GET /v1/custom-voices`) does not return.

### Minimal Repro

```python
from supertone import Supertone

client = Supertone(api_key="<valid_key>")
# This raises pydantic.ValidationError:
# "1 validation error for CustomVoice
#  description
#    field required (type=value_error.missing)"
voices = client.custom_voices.list_custom_voices()
```

### Workaround (historical)

`supertone-cli` previously bypassed the SDK and called the REST API directly via `httpx` in `src/supertone_cli/client.py:list_custom_voices()`. This was removed in ISSUE-028 once the upstream fix landed.

### Resolution

`supertone==0.2.1` ships a Pydantic model where `description` is `OptionalNullable[str] = UNSET` in `supertone/models/getcustomvoiceresponse.py`. ISSUE-028 reverted `list_custom_voices` to the SDK call and pinned `supertone>=0.2.1` in `pyproject.toml`.
