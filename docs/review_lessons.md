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
