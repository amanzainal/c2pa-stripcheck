"""Cover the rich console table, demo fixture writer, and run_platforms path."""

from __future__ import annotations

from c2pa_stripcheck import fixtures
from c2pa_stripcheck.classify import Verdict
from c2pa_stripcheck.report import render_console_table
from c2pa_stripcheck.runner import run_demo, run_platforms


def test_console_table_builds_a_row_per_result():
    matrix = run_demo()
    table = render_console_table(matrix)
    # rich.Table exposes row_count; one row per platform.
    assert table.row_count == len(matrix.rows)


def test_write_demo_fixtures_creates_all_files(tmp_path):
    paths = fixtures.write_demo_fixtures(tmp_path / "fx")
    assert set(paths) == {"signed", "stripped", "resigned", "soft_binding"}
    for p in paths.values():
        assert p.exists() and p.stat().st_size > 0


def test_run_platforms_against_stub_returns_untested(tmp_path):
    signed = tmp_path / "s.synthetic"
    signed.write_bytes(fixtures.make_signed_bytes())
    matrix = run_platforms(["reddit"], signed, tmp_path / "work")
    assert len(matrix.rows) == 1
    assert matrix.rows[0].verdict == "UNTESTED"


def test_run_demo_with_explicit_work_dir(tmp_path):
    matrix = run_demo(tmp_path / "wd")
    assert len(matrix.rows) == 4
    verdicts = {r.verdict for r in matrix.rows}
    assert Verdict.PRESERVED.value in verdicts
