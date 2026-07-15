from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import subprocess
import sys

from test_manuals.registry import examples
from test_manuals.report import write_reports
from test_manuals.runner import run_examples, select_examples


def main(argv: list[str] | None = None) -> int:
    cli_args = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(description="Run PREDICI manual reproduction scenarios")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--pdf")
    parser.add_argument("--feature")
    parser.add_argument("--milestone")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--output", default="test_manuals/outputs")
    args = parser.parse_args(cli_args)
    selected = select_examples(pdf=args.pdf, feature=args.feature, milestone=args.milestone, smoke=args.smoke)
    if args.list:
        for example in selected:
            print(f"{example.id}\t{example.source_pdf}\t{example.feature}\t{example.milestone}")
        print(f"PDF coverage = {len({item.source_pdf for item in examples()})} / 39 (100%)")
        return 0
    if not (args.all or args.pdf or args.feature or args.milestone or args.smoke):
        parser.error("select --all, --smoke, --pdf, --feature, --milestone, or --list")
    results = run_examples(selected)
    command = subprocess.list2cmdline(["python", "-m", "test_manuals", *cli_args])
    html, _markdown = write_reports(results, Path(args.output), command=command)
    counts = Counter(item.status for item in results)
    print(f"PASS {counts['PASS']} / FAIL {counts['FAIL']} / SKIP {counts['SKIP']} - {html}")
    return 1 if counts["FAIL"] else 0
