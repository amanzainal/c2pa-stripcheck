"""Tests for matrix aggregation, JSON round-trip, badge, and report rendering."""

from __future__ import annotations

import json

from c2pa_stripcheck.classify import Verdict
from c2pa_stripcheck.matrix import Matrix, badge_data, write_badge
from c2pa_stripcheck.report import render_markdown, write_markdown
from c2pa_stripcheck.runner import run_demo


def test_demo_matrix_has_all_four_verdicts():
    matrix = run_demo()
    verdicts = {r.verdict for r in matrix.rows}
    assert verdicts == {
        Verdict.PRESERVED.value,
        Verdict.STRIPPED.value,
        Verdict.RE_SIGNED.value,
        Verdict.SOFT_BINDING_RECOVERABLE.value,
    }


def test_matrix_counts_aggregate_correctly():
    matrix = run_demo()
    counts = matrix.counts()
    assert counts[Verdict.PRESERVED.value] == 1
    assert counts[Verdict.STRIPPED.value] == 1
    assert counts[Verdict.RE_SIGNED.value] == 1
    assert counts[Verdict.SOFT_BINDING_RECOVERABLE.value] == 1
    assert sum(counts.values()) == len(matrix.rows)


def test_matrix_has_version_metadata():
    matrix = run_demo()
    d = matrix.to_dict()
    assert d["schema_version"] >= 1
    assert d["tool_version"]
    assert d["generated_at"]


def test_matrix_json_round_trip(tmp_path):
    matrix = run_demo()
    path = matrix.write_json(tmp_path / "matrix.json")
    loaded = Matrix.load_json(path)
    assert loaded.counts() == matrix.counts()
    assert [r.verdict for r in loaded.rows] == [r.verdict for r in matrix.rows]
    # valid JSON
    json.loads(path.read_text())


def test_badge_reflects_mixed_results():
    matrix = run_demo()
    badge = badge_data(matrix)
    assert badge["schemaVersion"] == 1
    assert "preserve" in badge["message"]
    # Demo has both preserved and stripped -> yellow.
    assert badge["color"] == "yellow"


def test_badge_all_stripped_is_red():
    from c2pa_stripcheck.adapters import MockAdapter, MockBehavior
    from c2pa_stripcheck import fixtures
    from c2pa_stripcheck.probe import run_probe
    import tempfile
    from pathlib import Path

    matrix = Matrix()
    with tempfile.TemporaryDirectory() as wd:
        signed = Path(wd) / "s.synthetic"
        signed.write_bytes(fixtures.make_signed_bytes())
        for i in range(2):
            a = MockAdapter(name=f"s{i}", behavior=MockBehavior.STRIP)
            matrix.add(run_probe(a, signed, Path(wd) / f"w{i}"))
    assert badge_data(matrix)["color"] == "red"


def test_write_badge_file(tmp_path):
    matrix = run_demo()
    p = write_badge(matrix, tmp_path / "badge.json")
    data = json.loads(p.read_text())
    assert data["label"] == "C2PA preserved"


def test_markdown_report_renders_all_rows():
    matrix = run_demo()
    md = render_markdown(matrix)
    assert "Platform Behavior Matrix" in md
    # Every platform display name appears.
    for r in matrix.rows:
        assert r.display_name in md
    # Verdict symbols present.
    assert "✅" in md and "❌" in md and "🔁" in md and "🔗" in md


def test_markdown_report_mentions_soft_binding_resolution():
    md = render_markdown(run_demo())
    assert "Soft-Binding Resolution API" in md
    assert "TrustMark" in md


def test_write_markdown_file(tmp_path):
    matrix = run_demo()
    p = write_markdown(matrix, tmp_path / "MATRIX.md")
    text = p.read_text()
    assert text.startswith("# C2PA Content Credentials")
