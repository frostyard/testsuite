# frostyard testsuite

BDD suites that validate [snosi](https://github.com/frostyard/snosi) bootc
images. Run by [`frostyard/lab`](https://github.com/frostyard/lab) on every
published image digest.

---

## The execution model

Suites run **inside the image under test**. The lab boots the bootc OCI image as
a nested systemd container and runs `behave` against that live system:

```
podman run --systemd=always --privileged … <image>@<digest> /sbin/init
  └─ apt-get install python3-behave
  └─ behave tests/<suite>/features
```

So there is no SSH, no serial console, and no remote transport in this repo. A
probe is a subprocess against the local root filesystem, which means scenarios
read exactly like the assertions a person would make on a running machine.

**What that model cannot see**, and what therefore does not belong here:

- the kernel — a container runs the host's
- a graphical seat — no seat0, no framebuffer, so GDM cannot start a session
- disk layout — EROFS, dm-verity, Secure Boot, TPM/LUKS `/var`, A/B updates

Those need a real boot and belong to the lab's VM lane.

---

## Layout

```
tests/
├── shared/
│   ├── host.py     probe helpers: run(), have(), os_release(), failed_units()
│   └── steps.py    step vocabulary shared by every suite
├── smoke/features/
│   ├── boot.feature        boots to usable systemd, no unexpected failures
│   ├── identity.feature    os-release provenance and sysext level
│   ├── toolchain.feature   shipped binaries are present and runnable
│   ├── desktop.feature     graphical stack (skipped on headless variants)
│   ├── environment.py
│   └── steps/
├── system/features/   (empty — bootc/composefs contracts)
└── sysext/features/   (empty — systemd-sysext + updex behaviour)
```

A suite directory with features in it is automatically runnable; the lab's
pipeline already accepts `smoke`, `system`, and `sysext`.

---

## Running it

Against a live snosi machine, from a checkout:

```bash
PYTHONPATH=. python3 -m behave tests/smoke/features/ --no-capture --tags ~@wip
```

Against an image, the way the lab does it:

```bash
podman run --detach --systemd=always --privileged --cgroupns=host \
  --security-opt seccomp=unconfined \
  --tmpfs /run:rw,mode=755,size=512m --tmpfs /tmp:rw,mode=1777,size=512m \
  --mount type=bind,source=/sys,destination=/sys,ro \
  --name probe ghcr.io/frostyard/snow:latest /sbin/init

podman cp . probe:/testsuite
podman exec probe bash -c 'apt-get update -qq &&
  apt-get install -y -qq --no-install-recommends python3-behave'
podman exec -e PYTHONPATH=/testsuite -e SNOSI_VARIANT=snow probe \
  python3 -m behave /testsuite/tests/smoke/features/ --no-capture --tags ~@wip
```

---

## Environment

| Variable | Meaning |
|---|---|
| `SNOSI_VARIANT` | `snow`, `snowfield`, `cayo`, … Gates variant-specific scenarios. |
| `SNOSI_IMAGE` | Full pinned reference of the image under test. Logged, not asserted on. |

`GRAPHICAL_VARIANTS` in `tests/shared/host.py` decides which variants get the
desktop scenarios; everything else skips them. One suite runs unmodified across
the whole image family.

---

## Conventions

**behave is 1.2.6**, from Debian trixie's `python3-behave`. Using the distro
package rather than pip keeps the harness on the image's own Python and avoids a
PEP 668 bootstrap. It also fixes the tag syntax: negation is `~@wip`, not the
`not @wip` form that behave 1.3 introduced.

**Allowlists are empirical.** `EXPECTED_CONTAINER_FAILURES` in
`tests/smoke/features/steps/smoke_steps.py` is exactly the set of units observed
failing on a clean nested boot — not a set of units predicted to fail. Every
entry states why it cannot pass. A speculative allowlist is how a real
regression gets tolerated forever; if a unit stops failing, delete its entry.

**Assert on the shipped image, never a modified one.** The harness installs
`python3-behave` into the running container, and nothing else. A test that needs
a package installed to pass is testing something the image does not ship.

**Tag `@wip` for anything that should not gate.** The lab excludes it by default.
