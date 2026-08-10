# Repository policy

[`repository.json`](repository.json) is the source of truth for structural
repository requirements. `required_paths` lists assets that must exist, while
each `required_globs` entry declares a file pattern and its minimum match count.

Run the policy locally from the repository root:

```bash
python3 policies/check_repository.py
```

The evaluator uses only the Python standard library. It returns zero when the
repository complies, one for policy violations, and two for an invalid policy
document. Pull-request CI and nightly compliance both run the evaluator and its
unit tests.
