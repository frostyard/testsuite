"""Evaluate the repository policy without third-party dependencies."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


class PolicyConfigurationError(ValueError):
    """Raised when a policy document is not valid."""


@dataclass(frozen=True)
class GlobRequirement:
    pattern: str
    minimum: int


@dataclass(frozen=True)
class RepositoryPolicy:
    required_paths: tuple[str, ...]
    required_globs: tuple[GlobRequirement, ...]


def _validate_relative(value: str, field: str) -> None:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise PolicyConfigurationError(f"{field} must stay within the repository: {value}")


def load_policy(path: Path) -> RepositoryPolicy:
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise PolicyConfigurationError("the policy must be a JSON object")

    expected_keys = {"version", "required_paths", "required_globs"}
    if set(document) != expected_keys:
        raise PolicyConfigurationError(
            f"policy keys must be exactly: {', '.join(sorted(expected_keys))}"
        )
    if document["version"] != 1:
        raise PolicyConfigurationError("unsupported policy version")

    required_paths = document["required_paths"]
    if not isinstance(required_paths, list) or not all(
        isinstance(item, str) and item for item in required_paths
    ):
        raise PolicyConfigurationError("required_paths must be a list of non-empty strings")
    for required_path in required_paths:
        _validate_relative(required_path, "required path")

    raw_globs = document["required_globs"]
    if not isinstance(raw_globs, list):
        raise PolicyConfigurationError("required_globs must be a list")

    required_globs = []
    for index, raw_glob in enumerate(raw_globs):
        if not isinstance(raw_glob, dict) or set(raw_glob) != {"pattern", "minimum"}:
            raise PolicyConfigurationError(
                f"required_globs[{index}] must contain pattern and minimum"
            )
        pattern = raw_glob["pattern"]
        minimum = raw_glob["minimum"]
        if not isinstance(pattern, str) or not pattern:
            raise PolicyConfigurationError(
                f"required_globs[{index}].pattern must be a non-empty string"
            )
        if not isinstance(minimum, int) or isinstance(minimum, bool) or minimum < 1:
            raise PolicyConfigurationError(
                f"required_globs[{index}].minimum must be a positive integer"
            )
        _validate_relative(pattern, f"required_globs[{index}].pattern")
        required_globs.append(GlobRequirement(pattern=pattern, minimum=minimum))

    return RepositoryPolicy(
        required_paths=tuple(required_paths),
        required_globs=tuple(required_globs),
    )


def evaluate_policy(root: Path, policy: RepositoryPolicy) -> list[str]:
    violations = []
    for required_path in policy.required_paths:
        if not (root / required_path).exists():
            violations.append(f"required path is missing: {required_path}")

    for requirement in policy.required_globs:
        match_count = sum(1 for path in root.glob(requirement.pattern) if path.is_file())
        if match_count < requirement.minimum:
            violations.append(
                f"{requirement.pattern} matched {match_count} files; "
                f"minimum is {requirement.minimum}"
            )

    return violations


def main(argv: Sequence[str] | None = None) -> int:
    repository_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=repository_root)
    parser.add_argument(
        "--policy",
        type=Path,
        default=repository_root / "policies" / "repository.json",
    )
    args = parser.parse_args(argv)

    try:
        policy = load_policy(args.policy)
        violations = evaluate_policy(args.root, policy)
    except (OSError, json.JSONDecodeError, PolicyConfigurationError) as error:
        print(f"Policy configuration error: {error}", file=sys.stderr)
        return 2

    if violations:
        for violation in violations:
            print(f"Policy violation: {violation}", file=sys.stderr)
        return 1

    print(
        f"Repository policy passed: {len(policy.required_paths)} required paths and "
        f"{len(policy.required_globs)} required glob"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
