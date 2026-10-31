from __future__ import annotations

import json
import sys
from dataclasses import fields

from .checks import DesignInput, run_checks


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 -m eurocode3.cli input.json", file=sys.stderr)
        return 2
    with open(sys.argv[1], encoding="utf-8") as source:
        values = json.load(source)
    allowed = {item.name for item in fields(DesignInput)}
    data = DesignInput(**{key: value for key, value in values.items() if key in allowed})
    report = run_checks(data)
    for item in report.checks:
        print(f"{'PASS' if item.passed else 'FAIL':4} | {item.name:28} | "
              f"{item.utilization:.3f} | {item.note}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
