import csv
import json

from test_manuals.cli import main
from test_manuals.registry import examples


def test_manual_registry_has_unique_39_pdf_coverage():
    registered = examples()
    assert len(registered) == 39
    assert len({item.id for item in registered}) == 39
    assert len({item.source_pdf for item in registered}) == 39
    assert all(item.milestone.startswith("M") for item in registered)


def test_manual_list_and_smoke_generate_reports(tmp_path, capsys):
    assert main(["--list"]) == 0
    assert "PDF coverage = 39 / 39 (100%)" in capsys.readouterr().out
    assert main(["--smoke", "--split", "--output", str(tmp_path)]) == 0
    assert (tmp_path / "report.html").exists()
    assert (tmp_path / "report.md").exists()
    assert (tmp_path / "README.md").exists()
    assert (tmp_path / "results.json").exists()
    assert (tmp_path / "results.csv").exists()
    data = json.loads((tmp_path / "results.json").read_text(encoding="utf-8"))
    assert data["summary"]["selected_pdfs"] == 39
    assert data["summary"]["registered_pdfs"] == 39
    assert data["summary"]["fail"] == 0
    assert len(data["results"]) == 39
    with (tmp_path / "results.csv").open(encoding="utf-8-sig", newline="") as stream:
        assert len(list(csv.DictReader(stream))) == 39
    assert "[39](39/README.md)" in (tmp_path / "README.md").read_text(encoding="utf-8")
    for number in (1, 39):
        directory = tmp_path / str(number)
        assert (directory / "run_test.ps1").exists()
        assert (directory / "run_test.cmd").exists()
        assert "param([switch]$NoOpen)" in (directory / "run_test.ps1").read_text(encoding="utf-8-sig")
        individual = json.loads((directory / "results.json").read_text(encoding="utf-8"))
        assert individual["summary"]["examples"] == 1
        assert individual["results"][0]["status"] == "PASS"


def test_v2_medium_benchmarks_pass():
    from predici_clone.validation.benchmark_runner import run_benchmarks

    results = run_benchmarks("medium")
    assert len(results) == 10
    assert all(result.success for result in results)
