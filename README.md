<!-- readme-kind: infrastructure -->
# frostyard testsuite

[![CI](https://github.com/frostyard/testsuite/actions/workflows/ci.yml/badge.svg)](https://github.com/frostyard/testsuite/actions/workflows/ci.yml)

The BDD suites that validate [snosi](https://github.com/frostyard/snosi) bootc
images. [`frostyard/lab`](https://github.com/frostyard/lab) runs them inside
each published image digest, in the image booted as a nested systemd container,
so every scenario asserts on a live machine rather than on a copy of its files.
A change reaches lab by a merge to `main`.

**Status:** in production.

**Documentation:** [docs/README.md](docs/README.md)

## What is here

| Path | What it is |
| --- | --- |
| `tests/smoke/features/` | The boot, identity, toolchain, desktop and headless suites that lab runs |
| `tests/shared/` | Probe helpers (`host.py`) and the step vocabulary (`steps.py`) every suite shares |
| `tests/unit/` | Offline pytest tests of the probes, the steps and the feature-discovery checker |
| `tests/e2e/` | An ACMM discovery marker, not a suite: it holds no features |
| `policies/` | The repository policy, its checker, and the feature-discovery checker |
| `scripts/` | The template gate and the corrections gate that `make verify` runs |
| `test/` | Node tests of the template gate |
| `docs/` | The execution model, scenario authoring, review, quality and decisions |

## Use

Run a suite against a live snosi machine, from a checkout:

```bash
PYTHONPATH=. python3 -m behave tests/smoke/features/ --no-capture --tags ~@wip
```

The execution model, the `podman run` that the lab uses, the environment
variables and the conventions are in the
[execution model](docs/design/execution-model.md). To add a feature or a step,
follow [authoring a testsuite scenario](docs/authoring-scenarios.md).

## Develop

```bash
mise install                                          # the pinned Node
sudo apt-get install python3-behave python3-pytest    # behave 1.2.6, pytest
make ci                                               # what CI runs
```

The full setup, the test suites and the review expectations are in
[CONTRIBUTING.md](CONTRIBUTING.md).

## Where to go next

- [AGENTS.md](AGENTS.md): the rules for agents and contributors.
- [docs/README.md](docs/README.md): the execution model, authoring, quality and decisions.
- [SECURITY.md](SECURITY.md): report a vulnerability privately.
- [LICENSE](LICENSE): MIT.
