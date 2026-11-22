# Rule: Scenarios

Reproduce a bug with a unit test first. Most bugs live in one function or in one answer from the cloud, and a unit test with a mocked client shows them on their own.

Write a scenario in `tests/scenarios` only when a unit test cannot reproduce the bug, because it appears only through Home Assistant itself: the coordinator's schedule over several cycles, a config entry's setup, retry or reload, entities created during setup, or cloud answers that fail only in a given order. #200 is one: entities stay unavailable only after Home Assistant restarts while the panel is offline and the panel answers again later.

- Keep scenarios few: one per bug that needs it, in the module for its concern, and never one for a bug a unit test already reproduces.
- The fix still gets unit tests for the code it changes; the scenario shows the bug as a user sees it.
