from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PROGRAM_NAME = "main_program13.py"


def _repository_root() -> Path:
    for candidate in (HERE, *HERE.parents):
        if (candidate / "test_manuals" / "__init__.py").exists():
            return candidate
    raise RuntimeError("Could not locate the repository root containing test_manuals")


sys.path.insert(0, str(_repository_root()))

from test_manuals.registry import examples
from test_manuals.report import write_reports
from test_manuals.runner import run_examples


def main() -> int:
    input_data = json.loads((HERE / "input.json").read_text(encoding="utf-8"))
    example_id = input_data["examples"][0]["id"]
    selected = tuple(example for example in examples() if example.id == example_id)
    if len(selected) != 1:
        raise RuntimeError(f"Expected one registered example for {example_id!r}, found {len(selected)}")

    results = run_examples(selected)
    write_reports(results, HERE, command=f"python {PROGRAM_NAME}", program_name=PROGRAM_NAME)
    counts = Counter(item.status for item in results)
    print(f"PASS {counts['PASS']} / FAIL {counts['FAIL']} / SKIP {counts['SKIP']} - {HERE / 'report.html'}")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
