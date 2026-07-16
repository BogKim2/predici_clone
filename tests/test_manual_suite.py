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
    assert (tmp_path / "result.md").exists()
    assert (tmp_path / "README.md").exists()
    assert (tmp_path / "input.json").exists()
    assert (tmp_path / "result.json").exists()
    assert (tmp_path / "result.csv").exists()
    assert (tmp_path / "summary.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert not (tmp_path / "results.json").exists()
    assert not (tmp_path / "results.csv").exists()
    assert not (tmp_path / "report.md").exists()
    data = json.loads((tmp_path / "result.json").read_text(encoding="utf-8"))
    assert data["summary"]["selected_pdfs"] == 39
    assert data["summary"]["registered_pdfs"] == 39
    assert data["summary"]["fail"] == 0
    assert len(data["results"]) == 39
    with (tmp_path / "result.csv").open(encoding="utf-8-sig", newline="") as stream:
        assert len(list(csv.DictReader(stream))) == 39
    root_readme = (tmp_path / "README.md").read_text(encoding="utf-8")
    assert "![실행 결과 시각화](summary.png)" in root_readme
    assert "[39](39/README.md)" in root_readme
    for number in (1, 39):
        directory = tmp_path / str(number)
        program = directory / f"main_program{number}.py"
        assert program.exists()
        assert 'input_data = json.loads((HERE / "input.json")' in program.read_text(encoding="utf-8")
        assert not (directory / "run_test.ps1").exists()
        assert not (directory / "run_test.cmd").exists()
        assert (directory / "input.json").exists()
        assert (directory / "result.md").exists()
        assert (directory / "result.csv").exists()
        assert (directory / "result.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
        assert "![실행 결과 시각화](result.png)" in (directory / "README.md").read_text(encoding="utf-8")
        individual = json.loads((directory / "result.json").read_text(encoding="utf-8"))
        assert individual["summary"]["examples"] == 1
        assert individual["results"][0]["status"] == "PASS"


def test_v2_medium_benchmarks_pass():
    from predici_clone.validation.benchmark_runner import run_benchmarks

    results = run_benchmarks("medium")
    assert len(results) == 10
    assert all(result.success for result in results)
