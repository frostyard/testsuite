# Contributing

Thanks for looking at contributing to the frostyard testsuite. This repo holds
the BDD suites that validate [snosi](https://github.com/frostyard/snosi) bootc
images, run by [`frostyard/lab`](https://github.com/frostyard/lab). Please read
the [README](README.md) first — it explains the execution model, layout, and
conventions this project follows.

## Before you start

- Scenarios run **inside the image under test**, as a subprocess against the
  local root filesystem. There is no SSH, no serial console, and no remote
  transport. Anything that needs the kernel, a graphical seat, or disk layout
  (EROFS, dm-verity, Secure Boot, TPM/LUKS, A/B updates) belongs to the lab's
  VM lane instead, not here.
- Assert only on the shipped image. The harness installs `python3-behave` into
  the running container and nothing else — a scenario that needs another
  package installed to pass is testing something the image does not ship.

## Making changes

1. Fork the repository and create a branch for your change.
2. Add or update `.feature` files and step implementations under the
   appropriate `tests/<suite>/features` directory. Keep step vocabulary in
   `tests/shared/steps.py` and probe helpers in `tests/shared/host.py` where
   possible, rather than duplicating logic per suite.
3. Tag anything that should not gate the pipeline with `@wip`; the lab
   excludes it by default.
4. If you add an entry to `EXPECTED_CONTAINER_FAILURES`, make it empirical
   (observed on a clean nested boot) and document why it cannot pass. Remove
   entries once the underlying unit stops failing.

## Testing your change

Run the suite against a live snosi machine from a checkout:

```bash
PYTHONPATH=. python3 -m behave tests/smoke/features/ --no-capture --tags ~@wip
```

Or against an image the way the lab does — see the "Running it" section of the
[README](README.md#running-it) for the full `podman` invocation.

**behave is 1.2.6**, from Debian trixie's `python3-behave`. Install it from the
distro package rather than pip so the harness stays on the image's own Python;
note that tag negation is `~@wip`, not the `not @wip` form from behave 1.3.

## Submitting your change

Open a pull request describing what you changed and why, and include the
`behave` output showing the affected scenarios passing. Keep changes focused —
prefer several small, reviewable pull requests over one large one.
