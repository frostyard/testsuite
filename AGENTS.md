# Agent instructions

- Keep changes focused and reviewable; do not modify unrelated scenarios or helper code.
- Tests run inside the image under test. Assert only on what the shipped image provides, and do not add dependencies that must be installed for a scenario to pass.
- Put shared step vocabulary in `tests/shared/steps.py` and probe helpers in `tests/shared/host.py` when adding or updating scenarios.
- Tag scenarios that should not gate the pipeline with `@wip`; the lab excludes those by default.
- Validate test changes with `PYTHONPATH=. python3 -m behave tests/smoke/features/ --no-capture --tags ~@wip` when a live snosi machine or suitable container is available.
