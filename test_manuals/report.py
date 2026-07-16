from __future__ import annotations

import csv
from collections import Counter, defaultdict
from datetime import datetime, timezone
from html import escape
import json
from pathlib import Path
import platform
import textwrap

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from test_manuals.registry import examples
from test_manuals.runner import ManualResult


def _expected_values(result: ManualResult) -> dict[str, dict[str, float | None]]:
    return {
        name: {"minimum": bounds[0], "maximum": bounds[1]}
        for name, bounds in sorted(result.example.expected.items())
    }


def _result_record(result: ManualResult) -> dict[str, object]:
    return {
        "id": result.example.id,
        "title": result.example.title,
        "source_pdf": result.example.source_pdf,
        "feature": result.example.feature,
        "milestone": result.example.milestone,
        "status": result.status,
        "duration_seconds": round(result.duration, 6),
        "metrics": dict(sorted(result.metrics.items())),
        "expected": _expected_values(result),
        "reason": result.reason,
        "requires": list(result.example.requires),
        "speed": result.example.speed,
    }


def _input_record(result: ManualResult) -> dict[str, object]:
    return {
        "id": result.example.id,
        "title": result.example.title,
        "source_pdf": result.example.source_pdf,
        "feature": result.example.feature,
        "milestone": result.example.milestone,
        "expected": _expected_values(result),
        "requires": list(result.example.requires),
        "speed": result.example.speed,
    }


def _summary(results: tuple[ManualResult, ...]) -> dict[str, object]:
    registered_pdfs = len({item.source_pdf for item in examples()})
    selected_pdfs = len({item.example.source_pdf for item in results})
    statuses = Counter(item.status for item in results)
    return {
        "examples": len(results),
        "pass": statuses["PASS"],
        "fail": statuses["FAIL"],
        "skip": statuses["SKIP"],
        "duration_seconds": round(sum(item.duration for item in results), 6),
        "selected_pdfs": selected_pdfs,
        "registered_pdfs": registered_pdfs,
        "pdf_coverage_percent": round(100 * selected_pdfs / registered_pdfs, 2) if registered_pdfs else 0.0,
    }


def _group_summary(results: tuple[ManualResult, ...], attribute: str) -> list[dict[str, object]]:
    grouped: dict[str, list[ManualResult]] = defaultdict(list)
    for result in results:
        grouped[getattr(result.example, attribute)].append(result)
    rows = []
    for name, items in sorted(grouped.items()):
        statuses = Counter(item.status for item in items)
        rows.append({
            "name": name,
            "examples": len(items),
            "pdfs": len({item.example.source_pdf for item in items}),
            "pass": statuses["PASS"],
            "fail": statuses["FAIL"],
            "skip": statuses["SKIP"],
        })
    return rows


def _metric_text(result: ManualResult) -> str:
    return ", ".join(f"{name}={value:.12g}" for name, value in sorted(result.metrics.items())) or "-"


def _expected_text(result: ManualResult) -> str:
    values = []
    for name, (minimum, maximum) in sorted(result.example.expected.items()):
        lower = "-inf" if minimum is None else f"{minimum:.12g}"
        upper = "+inf" if maximum is None else f"{maximum:.12g}"
        values.append(f"{name}: [{lower}, {upper}]")
    return ", ".join(values) or "-"


def _markdown_table(rows: list[dict[str, object]], heading: str) -> list[str]:
    lines = [f"## {heading}", "", "| Name | Examples | PDFs | PASS | FAIL | SKIP |", "| --- | ---: | ---: | ---: | ---: | ---: |"]
    lines.extend(
        f"| {row['name']} | {row['examples']} | {row['pdfs']} | {row['pass']} | {row['fail']} | {row['skip']} |"
        for row in rows
    )
    return lines


def _html_group_table(rows: list[dict[str, object]]) -> str:
    body = "".join(
        f"<tr><td>{escape(str(row['name']))}</td><td>{row['examples']}</td><td>{row['pdfs']}</td>"
        f"<td>{row['pass']}</td><td>{row['fail']}</td><td>{row['skip']}</td></tr>"
        for row in rows
    )
    return (
        "<table><thead><tr><th>Name</th><th>Examples</th><th>PDFs</th><th>PASS</th>"
        f"<th>FAIL</th><th>SKIP</th></tr></thead><tbody>{body}</tbody></table>"
    )


def _write_summary_figure(
    summary: dict[str, object],
    feature_summary: list[dict[str, object]],
    path: Path,
) -> None:
    figure = Figure(figsize=(11, 5.5), constrained_layout=True, facecolor="white")
    FigureCanvasAgg(figure)
    status_axes, feature_axes = figure.subplots(1, 2)

    status_names = ["PASS", "FAIL", "SKIP"]
    status_values = [int(summary[name.lower()]) for name in status_names]
    status_colors = ["#16803c", "#c83232", "#c28a18"]
    status_bars = status_axes.bar(
        status_names,
        status_values,
        color=status_colors,
        edgecolor="#273142",
        linewidth=0.8,
        hatch=["//", "xx", ".."],
    )
    status_axes.bar_label(status_bars, padding=3, fontweight="bold")
    status_axes.set_title("Execution status", fontweight="bold")
    status_axes.set_ylabel("Scenario count")
    status_axes.set_ylim(0, max(status_values + [1]) * 1.18)
    status_axes.grid(axis="y", alpha=0.25)

    feature_names = [str(row["name"]) for row in feature_summary]
    feature_values = [int(row["examples"]) for row in feature_summary]
    feature_bars = feature_axes.barh(
        feature_names,
        feature_values,
        color="#3276b1",
        edgecolor="#273142",
        linewidth=0.6,
    )
    feature_axes.bar_label(feature_bars, padding=3, fontsize=9)
    feature_axes.set_title("Coverage by feature", fontweight="bold")
    feature_axes.set_xlabel("Scenario count")
    feature_axes.set_xlim(0, max(feature_values + [1]) * 1.18)
    feature_axes.grid(axis="x", alpha=0.25)

    figure.suptitle(
        f"Manual reproduction summary — {summary['selected_pdfs']} / "
        f"{summary['registered_pdfs']} PDFs",
        fontsize=15,
        fontweight="bold",
    )
    figure.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")


def _write_result_figure(result: ManualResult, path: Path) -> None:
    metrics = sorted(result.metrics.items())
    height = max(4.2, 2.6 + 0.7 * len(metrics))
    figure = Figure(figsize=(10, height), constrained_layout=True, facecolor="white")
    FigureCanvasAgg(figure)
    axes = figure.subplots()

    if metrics:
        names = [name for name, _value in metrics]
        values = [value for _name, value in metrics]
        positions = list(range(len(metrics)))
        color = "#16803c" if result.status == "PASS" else "#c83232"
        bars = axes.barh(
            positions,
            values,
            color=color,
            edgecolor="#273142",
            linewidth=0.8,
            alpha=0.9,
        )
        axes.set_yticks(positions, labels=names)
        axes.invert_yaxis()
        axes.bar_label(bars, labels=[f"{value:.6g}" for value in values], padding=4)

        candidates = [0.0, *values]
        has_expected_marker = False
        for position, (name, _value) in enumerate(metrics):
            minimum, maximum = result.example.expected.get(name, (None, None))
            if minimum is not None:
                axes.scatter(minimum, position, marker="|", s=260, color="#111827", zorder=3)
                candidates.append(minimum)
                has_expected_marker = True
            if maximum is not None:
                axes.scatter(maximum, position, marker="|", s=260, color="#111827", zorder=3)
                candidates.append(maximum)
                has_expected_marker = True
            if minimum is not None and maximum is not None:
                axes.plot([minimum, maximum], [position, position], color="#111827", linewidth=2, zorder=2)

        lower, upper = min(candidates), max(candidates)
        span = upper - lower or 1.0
        axes.set_xlim(min(0.0, lower - span * 0.08), upper + span * 0.2)
        axes.set_xlabel("Calculated value")
        axes.grid(axis="x", alpha=0.25)
        if has_expected_marker:
            axes.text(
                1.0,
                -0.13,
                "Black marker: expected boundary",
                transform=axes.transAxes,
                ha="right",
                fontsize=9,
                color="#4b5563",
            )
    else:
        axes.text(0.5, 0.5, "No metrics were produced", ha="center", va="center", fontsize=14)
        axes.set_axis_off()

    title = textwrap.fill(result.example.source_pdf, width=70)
    figure.suptitle(
        f"{result.status} — {title}",
        x=0.01,
        ha="left",
        fontsize=14,
        fontweight="bold",
    )
    axes.set_title(
        f"{result.example.feature} / {result.example.milestone}  •  {result.duration:.6f} seconds",
        loc="left",
        fontsize=9,
        color="#4b5563",
        pad=10,
    )
    figure.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")


def _remove_legacy_files(output: Path) -> None:
    for name in ("results.json", "results.csv", "report.md", "run_test.ps1", "run_test.cmd"):
        path = output / name
        if path.exists():
            path.unlink()


def write_reports(
    results: tuple[ManualResult, ...],
    output_directory: str | Path,
    *,
    command: str = "python -m test_manuals",
    program_name: str | None = None,
) -> tuple[Path, Path]:
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    _remove_legacy_files(output)
    generated_at = datetime.now(timezone.utc).isoformat()
    summary = _summary(results)
    feature_summary = _group_summary(results, "feature")
    milestone_summary = _group_summary(results, "milestone")
    records = [_result_record(item) for item in results]

    input_document = {
        "schema_version": 1,
        "description": "Inputs and expected ranges for manual reproduction scenarios.",
        "examples": [_input_record(item) for item in results],
    }
    input_path = output / "input.json"
    input_path.write_text(json.dumps(input_document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    document = {
        "schema_version": 1,
        "generated_at_utc": generated_at,
        "command": command,
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "summary": summary,
        "by_feature": feature_summary,
        "by_milestone": milestone_summary,
        "results": records,
    }
    json_path = output / "result.json"
    json_path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    csv_path = output / "result.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as stream:
        fieldnames = [
            "id", "source_pdf", "title", "feature", "milestone", "status", "duration_seconds",
            "metrics", "expected", "reason", "requires", "speed",
        ]
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            row = dict(record)
            for field in ("metrics", "expected", "requires"):
                row[field] = json.dumps(row[field], ensure_ascii=False, sort_keys=True)
            writer.writerow(row)

    markdown = [
        "# Manual reproduction report",
        "",
        f"- Generated (UTC): `{generated_at}`",
        f"- Command: `{command}`",
        f"- Environment: Python {document['environment']['python']} / {document['environment']['platform']}",
        f"- Result: PASS {summary['pass']} / FAIL {summary['fail']} / SKIP {summary['skip']}",
        f"- PDF coverage: {summary['selected_pdfs']} / {summary['registered_pdfs']} ({summary['pdf_coverage_percent']:.2f}%)",
        f"- Total duration: {summary['duration_seconds']:.6f} seconds",
        "",
    ]
    markdown.extend(_markdown_table(feature_summary, "By feature"))
    markdown.append("")
    markdown.extend(_markdown_table(milestone_summary, "By milestone"))
    markdown.extend(["", "## Results by PDF", ""])
    for result in results:
        reason = result.reason or "-"
        markdown.extend([
            f"### {result.example.source_pdf}",
            "",
            "| Field | Value |",
            "| --- | --- |",
            f"| Example | `{result.example.id}` - {result.example.title} |",
            f"| Classification | `{result.example.feature}` / `{result.example.milestone}` |",
            f"| Status | **{result.status}** |",
            f"| Duration | {result.duration:.6f} seconds |",
            f"| Metrics | `{_metric_text(result)}` |",
            f"| Expected | `{_expected_text(result)}` |",
            f"| Reason | {reason} |",
            "",
        ])
    markdown_path = output / "result.md"
    markdown_path.write_text("\n".join(markdown), encoding="utf-8")

    figure_name = "result.png" if len(results) == 1 else "summary.png"
    figure_path = output / figure_name
    if len(results) == 1:
        _write_result_figure(results[0], figure_path)
    else:
        _write_summary_figure(summary, feature_summary, figure_path)

    sections = []
    for result in results:
        sections.append(
            f"<section><h3>{escape(result.example.source_pdf)}</h3>"
            "<table><tbody>"
            f"<tr><th>Example</th><td><code>{escape(result.example.id)}</code> - {escape(result.example.title)}</td></tr>"
            f"<tr><th>Classification</th><td>{escape(result.example.feature)} / {escape(result.example.milestone)}</td></tr>"
            f"<tr><th>Status</th><td><span class='status {result.status.lower()}'>{result.status}</span></td></tr>"
            f"<tr><th>Duration</th><td>{result.duration:.6f} seconds</td></tr>"
            f"<tr><th>Metrics</th><td><code>{escape(_metric_text(result))}</code></td></tr>"
            f"<tr><th>Expected</th><td><code>{escape(_expected_text(result))}</code></td></tr>"
            f"<tr><th>Reason</th><td>{escape(result.reason or '-')}</td></tr>"
            "</tbody></table></section>"
        )
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Manual reproduction report</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:1180px;margin:0 auto;padding:24px;color:#202124;background:#f7f7f5}}
h1,h2,h3{{letter-spacing:0}} .meta{{color:#555}} .summary{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:20px 0}}
.summary div,section{{background:#fff;border:1px solid #d9d9d5;border-radius:6px;padding:14px}} .summary strong{{display:block;font-size:1.4rem}}
table{{border-collapse:collapse;width:100%;margin:10px 0 22px;background:#fff}} th,td{{border:1px solid #d9d9d5;padding:8px;text-align:left;vertical-align:top}} th{{background:#efefeb}}
section{{margin:12px 0}} section table{{margin:0}} section h3{{margin-top:0;overflow-wrap:anywhere}} code{{overflow-wrap:anywhere}}
.result-figure{{display:block;width:min(100%,1050px);margin:20px auto;border:1px solid #d9d9d5;border-radius:6px;background:#fff}}
.status{{font-weight:700}} .pass{{color:#18733b}} .fail{{color:#b3261e}} .skip{{color:#7a5901}}
</style></head><body>
<h1>Manual reproduction report</h1>
<p class="meta">Generated (UTC): {escape(generated_at)}<br>Command: <code>{escape(command)}</code><br>Python {document['environment']['python']} / {escape(str(document['environment']['platform']))}</p>
<div class="summary"><div><span>PASS</span><strong>{summary['pass']}</strong></div><div><span>FAIL</span><strong>{summary['fail']}</strong></div><div><span>SKIP</span><strong>{summary['skip']}</strong></div><div><span>PDF coverage</span><strong>{summary['selected_pdfs']} / {summary['registered_pdfs']}</strong><span>{summary['pdf_coverage_percent']:.2f}%</span></div><div><span>Duration</span><strong>{summary['duration_seconds']:.4f}s</strong></div></div>
<img class="result-figure" src="{figure_name}" alt="Manual reproduction result visualization">
<h2>By feature</h2>{_html_group_table(feature_summary)}
<h2>By milestone</h2>{_html_group_table(milestone_summary)}
<h2>Results by PDF</h2>{''.join(sections)}
</body></html>
"""
    html_path = output / "report.html"
    html_path.write_text(html, encoding="utf-8")

    readme_title = "test_manual_result" if len(results) != 1 else f"Test result: {results[0].example.source_pdf}"
    description = (
        "이 디렉터리는 39개 PDF 매뉴얼 재현 시나리오의 전체 실행 결과입니다."
        if len(results) != 1
        else f"이 디렉터리는 `{results[0].example.source_pdf}` 재현 시나리오의 개별 실행 결과입니다."
    )
    file_entries = [
        "- [input.json](input.json): 시나리오 입력 메타데이터와 기대 범위",
        "- [report.html](report.html): feature, milestone, PDF별 브라우저 보고서",
        "- [result.md](result.md): PDF별 지표와 기대 범위를 모두 포함한 Markdown 결과",
        "- [result.json](result.json): 실행 환경, 집계, 개별 결과를 포함한 구조화 결과",
        "- [result.csv](result.csv): PDF당 한 행으로 정리한 스프레드시트용 결과",
        f"- [{figure_name}]({figure_name}): README와 HTML에 포함된 결과 그림",
    ]
    if program_name is not None:
        file_entries.append(
            f"- [{program_name}]({program_name}): `input.json`을 읽어 이 시나리오를 다시 실행"
        )
    readme = [
        f"# {readme_title}",
        "",
        description,
        "",
        f"- 결과: **PASS {summary['pass']} / FAIL {summary['fail']} / SKIP {summary['skip']}**",
        f"- PDF 커버리지: **{summary['selected_pdfs']} / {summary['registered_pdfs']} ({summary['pdf_coverage_percent']:.2f}%)**",
        f"- 실행 명령: `{command}`",
        f"- 생성 시각(UTC): `{generated_at}`",
        "",
        "## 결과 그림",
        "",
        f"![실행 결과 시각화]({figure_name})",
        "",
        "## 파일",
        "",
        *file_entries,
        "",
        "## PDF와 시나리오 매핑",
        "",
        "| PDF | Example ID | Feature | Milestone | Status |",
        "| --- | --- | --- | --- | --- |",
    ]
    readme.extend(
        f"| {item.example.source_pdf} | `{item.example.id}` | `{item.example.feature}` | `{item.example.milestone}` | **{item.status}** |"
        for item in results
    )
    (output / "README.md").write_text("\n".join(readme) + "\n", encoding="utf-8")
    return html_path, markdown_path


def write_split_reports(results: tuple[ManualResult, ...], output_directory: str | Path) -> tuple[Path, ...]:
    output = Path(output_directory)
    directories = []
    index_rows = []
    for number, result in enumerate(results, start=1):
        directory = output / str(number)
        program_name = f"main_program{number}.py"
        command = f"python {program_name}"
        write_reports((result,), directory, command=command, program_name=program_name)

        program = f'''from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PROGRAM_NAME = "{program_name}"


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
        raise RuntimeError(f"Expected one registered example for {{example_id!r}}, found {{len(selected)}}")

    results = run_examples(selected)
    write_reports(results, HERE, command=f"python {{PROGRAM_NAME}}", program_name=PROGRAM_NAME)
    counts = Counter(item.status for item in results)
    print(f"PASS {{counts['PASS']}} / FAIL {{counts['FAIL']}} / SKIP {{counts['SKIP']}} - {{HERE / 'report.html'}}")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
'''
        (directory / program_name).write_text(program, encoding="utf-8")
        directories.append(directory)
        index_rows.append(
            f"| [{number}]({number}/README.md) | {result.example.source_pdf} | "
            f"`{result.example.id}` | `{result.example.feature}` | `{result.example.milestone}` | **{result.status}** |"
        )

    root_readme = output / "README.md"
    with root_readme.open("a", encoding="utf-8") as stream:
        stream.write("\n## 개별 테스트 폴더\n\n")
        stream.write("각 번호 폴더의 `main_program{번호}.py`를 실행하면 `input.json`을 읽어 해당 PDF 한 건만 다시 계산하고 결과와 그림을 같은 폴더에 저장합니다.\n\n")
        stream.write("| 번호 | PDF | Example ID | Feature | Milestone | Status |\n")
        stream.write("| ---: | --- | --- | --- | --- | --- |\n")
        stream.write("\n".join(index_rows) + "\n")
    return tuple(directories)
