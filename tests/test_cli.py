"""End-to-end CLI tests via the in-process entrypoint."""

from __future__ import annotations

import json

from c2pa_stripcheck.cli import main


def test_cli_demo_writes_outputs(tmp_path):
    out = tmp_path / "out"
    rc = main(["run", "--demo", "--out", str(out), "--quiet"])
    assert rc == 0
    assert (out / "matrix.json").exists()
    assert (out / "MATRIX.md").exists()
    assert (out / "badge.json").exists()
    data = json.loads((out / "matrix.json").read_text())
    assert len(data["rows"]) == 4


def test_cli_run_without_demo_or_platform_errors(tmp_path):
    rc = main(["run", "--out", str(tmp_path / "o"), "--quiet"])
    assert rc == 2


def test_cli_run_real_platform_without_asset_errors(tmp_path):
    rc = main(["run", "--platform", "instagram", "--out", str(tmp_path / "o")])
    assert rc == 2


def test_cli_matrix_rerender(tmp_path):
    out = tmp_path / "out"
    main(["run", "--demo", "--out", str(out), "--quiet"])
    rerendered = tmp_path / "rr"
    rc = main(["matrix", str(out / "matrix.json"), "--out", str(rerendered), "--quiet"])
    assert rc == 0
    assert (rerendered / "MATRIX.md").exists()


def test_cli_list_runs():
    assert main(["list"]) == 0


def test_cli_readers_runs():
    assert main(["readers"]) == 0
