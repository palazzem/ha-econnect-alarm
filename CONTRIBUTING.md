# Contributing to Home Assistant e-Connect integration

This document provides guidelines for contributing to project. Before you begin, please follow the
instructions below:

1. Prepare your [development environment](https://github.com/palazzem/ha-econnect-alarm#development).
2. Ensure that you have installed the `pre-commit` hooks.
3. Run `tox` to execute the full test suite.

By following these steps, you can ensure that your contributions are of the highest quality and are properly tested
before they are merged into the project.

## Issues

If you're experiencing a problem or have a suggestion, we encourage you to open a
[new issue](https://github.com/palazzem/ha-econnect-alarm/issues/new/choose).
Please make sure to select the most appropriate type from the options provided:

- **Bug Report**: If you've identified an issue with an existing feature that isn't performing as documented or expected,
please select this option. This will help us identify and rectify problems more efficiently.

- **Feature Request**: Opt for this if you have an idea for a new feature or an enhancement to the current ones.
Additionally, if you feel that a certain feature could be optimized or modified to better suit specific scenarios, this is
the right category to bring it to our attention.

- **Join Discord channel**: If you are unsure, or if you have a general question, please join our [Discord channel](https://discord.gg/NSmAPWw8tE).

After choosing an issue type, a pre-formatted template will appear. It's essential to provide as much detail as possible
within this template. Your insights and contributions help in improving the project, and we genuinely appreciate your effort.

## Pull Requests

### PR Title

We follow the [conventional commit convention](https://www.conventionalcommits.org/en/v1.0.0/) for our PR titles.
The title should adhere to the structure below:

```
<type>[optional scope]: <description>
```

The common types are:
- `feat` (enhancements)
- `fix` (bug fixes)
- `docs` (documentation changes)
- `perf` (performance improvements)
- `refactor` (major code refactorings)
- `tests` (changes to tests)
- `tools` (changes to package spec or tools in general)
- `ci` (changes to our CI)
- `deps` (changes to dependencies)

If your change breaks backwards compatibility, indicate so by adding `!` after the type.

Examples:
- `feat(cli): add Transcribe command`
- `fix: ensure hashing function returns correct value for random input`
- `feat!: remove deprecated API` (a change that breaks backwards compatibility)

### PR Description

After opening a new pull request, a pre-formatted template will appear. It's essential to provide as much detail as possible
within this template. A good description and can speed up the review process to get your code merged.
