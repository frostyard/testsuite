"""Require Behave feature discovery to select at least one scenario."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Sequence


def discover(features_dir: Path) -> tuple[int, int, str | None]:
    if not features_dir.is_dir():
        return 0, 0, f"features directory is missing: {features_dir}"

    with tempfile.TemporaryDirectory(prefix="feature-discovery-") as temporary:
        output_path = Path(temporary) / "behave.json"
        command = [
            sys.executable,
            "-m",
            "behave",
            str(features_dir),
            "--dry-run",
            "--no-capture",
            "--tags",
            "~@wip",
            "-f",
            "json",
            "-o",
            str(output_path),
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            diagnostic = (result.stderr or result.stdout).strip()
            if diagnostic:
                return 0, 0, f"behave failed (exit {result.returncode}): {diagnostic}"
            return 0, 0, f"behave failed (exit {result.returncode})"

        if not output_path.is_file():
            return 0, 0, "behave did not produce a JSON discovery result"

        try:
            data = json.loads(output_path.read_text(encoding="utf-8") or "[]")
        except json.JSONDecodeError as error:
            return 0, 0, f"behave returned invalid JSON: {error}"

        if not isinstance(data, list):
            return 0, 0, "behave returned unexpected JSON discovery data"

        features = sum(1 for feature in data if isinstance(feature, dict))
        scenarios = 0
        for feature in data:
            if not isinstance(feature, dict):
                continue
            for element in feature.get("elements", []):
                if not isinstance(element, dict):
                    continue
                if element.get("type") == "scenario" and element.get("status") != "skipped":
                    scenarios += 1

        return features, scenarios, None


def main(argv: Sequence[str] | None = None) -> int:
    repository_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "features_dir",
        nargs="?",
        type=Path,
        default=repository_root / "tests" / "smoke" / "features",
    )
    args = parser.parse_args(argv)

    features, scenarios, error = discover(args.features_dir)
    print(f"feature discovery: {features} features, {scenarios} scenarios selected")

    if error:
        print(f"feature discovery failed: {error}", file=sys.stderr)
        return 1
    if scenarios == 0:
        print(
            f"feature discovery failed: 0 scenarios selected in {args.features_dir}",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
