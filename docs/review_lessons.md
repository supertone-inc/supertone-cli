# Review Lessons

Preventable patterns extracted during code review. Each entry has a stable ID,
a category (Code Quality / Security / Testing / Architecture), a Frequency
counter, and an Observed-In list.

---

## [RL-001] Date/datetime passed to API without normalizing to the format the endpoint requires

- Category: Code Quality
- Frequency: 1
- Observed-In: ISSUE-029 (usage analytics forwarded `YYYY-MM-DD` to an endpoint
  requiring full ISO-8601 datetime, causing a server 400)
- Prevention: When a CLI flag accepts a human-friendly date but the SDK/endpoint
  needs a stricter format, normalize at the client boundary and decide
  start-of-day vs end-of-day semantics explicitly. Catch at implementation time
  by reading the SDK/endpoint contract for each datetime argument.

## [RL-002] Format/separator detection uses an exact-case substring check

- Category: Code Quality
- Frequency: 1
- Observed-In: ISSUE-029 (`"T" in value` misses ISO-8601's permitted lowercase
  `t` separator)
- Prevention: When branching on a format marker that a spec allows in multiple
  forms, normalize case (or match both) before testing. Low impact when inputs
  are constrained, but cheap to guard at write time.

## [RL-003] Test mocks expose attributes the real SDK response does not

- Category: Testing
- Frequency: 1
- Observed-In: ISSUE-030 (custom-voice fallback tests build `MagicMock`s with
  `gender`/`age`/`language`/`use_cases`, but the real `GetCustomVoiceResponse`
  only carries `voice_id`/`name`/`description`; the test would not catch a
  regression that assumes a non-existent required attribute)
- Prevention: When mocking an SDK response, mirror the real model's actual field
  set (check `model_fields`). Prefer constructing the real response object or a
  mock limited to the documented fields, so the test fails if production code
  starts depending on attributes the endpoint never returns.

## [RL-004] New branch in a helper is only exercised via one detection path

- Category: Testing
- Frequency: 2
- Observed-In: ISSUE-030 (`_is_not_found_error` has a typed-isinstance branch
  and a `status_code == 404` branch; tests only cover the latter); ISSUE-031
  (the new `if stream and model is None` branch's load-bearing guarantee — that
  config `default_model` is bypassed for streaming — was exercised by only one
  path and not directly tested until review added it)
- Prevention: When a helper has multiple detection branches (typed exception vs
  duck-typed attribute), add a direct unit test per branch rather than relying
  on one integration path to cover all of them.

---

## [RL-005] Auto-selection logic hardcodes a literal that duplicates a capability set

- Category: Architecture
- Frequency: 1
- Observed-In: ISSUE-031 (the streaming default hardcodes `"sona_speech_1"` at
  `tts.py:266`, duplicating the `_STREAM_MODELS` set at `tts.py:36`; if a second
  streaming model is added, the validator would accept it while the auto-default
  still forces `sona_speech_1`)
- Prevention: When defaulting to "the only X that supports Y", derive the value
  from the capability set the validator already uses, or add a `keep in sync`
  comment, so the default and the validator cannot diverge as the set grows.
