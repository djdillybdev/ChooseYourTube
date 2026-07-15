"""Enforce independent line and branch coverage thresholds.

Coverage.py's built-in ``fail_under`` applies to its combined metric when branch
coverage is enabled. The release contract requires both dimensions to clear the
threshold independently, so CI and local verification use this small checker.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", nargs="?", default="coverage.json")
    parser.add_argument("--minimum", type=float, default=80.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report_path = Path(args.report)
    if not report_path.is_file():
        raise SystemExit(f"Coverage report not found: {report_path}")

    totals = json.loads(report_path.read_text())["totals"]
    lines = float(totals["percent_statements_covered"])
    branches = float(totals["percent_branches_covered"])
    print(f"Backend coverage: lines={lines:.2f}% branches={branches:.2f}%")

    failures = [
        f"{name} coverage {value:.2f}% is below {args.minimum:.2f}%"
        for name, value in (("line", lines), ("branch", branches))
        if value < args.minimum
    ]
    if failures:
        raise SystemExit("; ".join(failures))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
