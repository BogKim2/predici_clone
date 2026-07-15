from __future__ import annotations

from collections import Counter
from html import escape
from pathlib import Path

from test_manuals.runner import ManualResult


def write_reports(results: tuple[ManualResult, ...], output_directory: str | Path) -> tuple[Path, Path]:
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    statuses = Counter(item.status for item in results)
    rows = "".join(
        f"<tr><td>{escape(item.example.source_pdf)}</td><td>{escape(item.example.title)}</td><td>{item.status}</td><td>{item.duration:.4f}</td><td>{escape(str(item.metrics))}</td><td>{escape(item.reason)}</td></tr>"
        for item in results
    )
    html = f"<!doctype html><meta charset='utf-8'><title>Manual reproduction report</title><h1>Manual reproduction report</h1><p>PASS {statuses['PASS']} / FAIL {statuses['FAIL']} / SKIP {statuses['SKIP']}</p><table><thead><tr><th>PDF</th><th>Example</th><th>Status</th><th>Seconds</th><th>Metrics</th><th>Reason</th></tr></thead><tbody>{rows}</tbody></table>"
    html_path = output / "report.html"
    html_path.write_text(html, encoding="utf-8")
    markdown = ["# Manual reproduction report", "", f"PASS {statuses['PASS']} / FAIL {statuses['FAIL']} / SKIP {statuses['SKIP']}", "", "| PDF | Example | Status | Seconds |", "| --- | --- | --- | ---: |"]
    markdown.extend(f"| {item.example.source_pdf} | {item.example.title} | {item.status} | {item.duration:.4f} |" for item in results)
    markdown_path = output / "report.md"
    markdown_path.write_text("\n".join(markdown) + "\n", encoding="utf-8")
    return html_path, markdown_path
