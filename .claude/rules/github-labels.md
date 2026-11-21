# Rule: GitHub Labels

Every issue and every PR you create gets its labels when you create it. Pick them from `gh label list`; each label's description states what it means.

- `type:` the kind of work. Exactly one, always required.
- `area:` the tree or folder the work changes. Every one that applies.
- `domain:` the part of the integration the work serves. Every one that applies.
- `touches:` a concern that brings in a closer review: security, or the e-Connect/Metronet cloud API. Every one that applies.
- `waiting:` who must answer before the work goes on. Set it while they hold the work, remove it once they answer.
- `breaking-change`: users must change their configuration or automations after upgrading.
- `spec`: an approved specification.
- `wont-do`: we decided not to do the work. Set it when you close the issue as not planned.
