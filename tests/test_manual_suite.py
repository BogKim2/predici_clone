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
    assert main(["--smoke", "--output", str(tmp_path)]) == 0
    assert (tmp_path / "report.html").exists()
    assert (tmp_path / "report.md").exists()


def test_v2_medium_benchmarks_pass():
    from predici_clone.validation.benchmark_runner import run_benchmarks

    results = run_benchmarks("medium")
    assert len(results) == 10
    assert all(result.success for result in results)
