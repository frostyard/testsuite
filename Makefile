# The make gate (frostyard core ADR-0043, ADR-0044, ADR-0071 row B4).
# These targets need no cluster, no credentials, no root and no image: they
# check the repository, not the images that frostyard/lab tests with it.
#
#   make verify          the baseline gate: verify-template and verify-python.
#                        It does not change the tracked files.
#   make verify-template the template gate (agent symlinks, docs index,
#                        risk-path list, corrections, vendored core copies)
#                        and its Node tests.
#   make verify-python   the repository policy check, the policy unittest
#                        suite, the pytest unit suite of tests/unit, and the
#                        behave feature-discovery check of tests/smoke/features.
#   make check           the developer gate; the same as verify.
#   make ci              verify, plus the corrections records check
#                        against BASE when BASE is set (CI passes the pull
#                        request base commit): no record removed or renamed,
#                        and the old corrections file does not come back.
#
# behave and pytest are not pinned here: they come from the Debian or Ubuntu
# packages `python3-behave` and `python3-pytest`, and behave is 1.2.6, the
# same version the images under test install. mise therefore pins only Node.
NODE_MAJOR := $(shell node -p "process.versions.node.split('.')[0]" 2>/dev/null)
PYTHON ?= python3

.PHONY: verify verify-template verify-python check ci

verify: verify-template verify-python

# Node.js exits 0 when its test glob matches nothing (ADR-0010), so each
# Node test recipe first requires at least 1 test file.
verify-template:
	@if ! ls test/*.test.mjs >/dev/null 2>&1; then echo "FAIL: no files match test/*.test.mjs; node --test would run zero tests"; exit 1; fi
	@if ! command -v node >/dev/null 2>&1; then echo "FAIL: make verify-template requires Node.js 22 or later (mise install)"; exit 1; fi
	@if [ "$(NODE_MAJOR)" = "" ] || [ "$(NODE_MAJOR)" -lt 22 ]; then echo "FAIL: make verify-template requires Node.js 22 or later (found: $$(node --version 2>/dev/null || echo missing))"; exit 1; fi
	node scripts/check-template.mjs
	node --test test/*.test.mjs

# Each command fails on an empty input (ADR-0010): `unittest discover` exits 5
# when it runs no test (Python 3.12 and later), pytest exits 5 when it collects
# none, and check_feature_discovery.py fails when it selects no scenario.
verify-python:
	$(PYTHON) -m unittest discover -s policies -p 'test_*.py'
	$(PYTHON) policies/check_repository.py
	PYTHONPATH=. $(PYTHON) -m pytest -q tests/unit
	PYTHONPATH=. $(PYTHON) policies/check_feature_discovery.py tests/smoke/features/

check: verify

ci: verify
	@if [ -n "$(BASE)" ]; then node scripts/check-corrections.mjs --base "$(BASE)"; fi
