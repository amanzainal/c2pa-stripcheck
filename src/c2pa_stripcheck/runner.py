"""High-level runners that produce a populated :class:`Matrix`.

* :func:`run_demo` — uses the offline mock adapter with several behaviors and the
  synthetic signed fixture. Fully offline, deterministic, no accounts/GPU.
* :func:`run_platforms` — probes named real-platform adapters (stubs until wired
  up) against a caller-provided signed asset.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from . import fixtures
from .adapters import MockAdapter, MockBehavior, get_adapter
from .matrix import Matrix
from .probe import run_probe

#: The demo line-up: each fake platform exhibits one of the four behaviors so the
#: matrix shows every verdict at once.
DEMO_PLATFORMS = [
    ("preserve-co", "Preserve Co (demo)", MockBehavior.PRESERVE),
    ("strip-net", "StripNet (demo)", MockBehavior.STRIP),
    ("resign-app", "ReSignApp (demo)", MockBehavior.RESIGN),
    ("softbind-social", "SoftBind Social (demo)", MockBehavior.SOFT_BINDING),
]


def run_demo(work_dir: str | Path | None = None) -> Matrix:
    """Run the offline demo against synthetic fixtures; return a populated Matrix."""
    matrix = Matrix()
    with _maybe_tempdir(work_dir) as wd:
        signed = Path(wd) / "signed_input.synthetic"
        signed.write_bytes(fixtures.make_signed_bytes(soft_binding_id="demo-wm-001"))
        for name, display, behavior in DEMO_PLATFORMS:
            adapter = MockAdapter(
                name=name, display_name=display, behavior=behavior,
                notes=f"Demo mock with behavior={behavior.value}.",
            )
            matrix.add(run_probe(adapter, signed, Path(wd) / name))
    return matrix


def run_platforms(
    platforms: list[str],
    signed_asset: str | Path,
    work_dir: str | Path | None = None,
) -> Matrix:
    """Probe real-platform adapters by name against ``signed_asset``."""
    matrix = Matrix()
    with _maybe_tempdir(work_dir) as wd:
        for name in platforms:
            adapter = get_adapter(name)
            matrix.add(run_probe(adapter, signed_asset, Path(wd) / name))
    return matrix


class _maybe_tempdir:
    """Context manager: use ``work_dir`` if given, else a TemporaryDirectory."""

    def __init__(self, work_dir: str | Path | None) -> None:
        self._given = work_dir
        self._tmp: tempfile.TemporaryDirectory | None = None

    def __enter__(self) -> str:
        if self._given is not None:
            Path(self._given).mkdir(parents=True, exist_ok=True)
            return str(self._given)
        self._tmp = tempfile.TemporaryDirectory(prefix="c2pa-stripcheck-")
        return self._tmp.name

    def __exit__(self, *exc) -> None:
        if self._tmp is not None:
            self._tmp.cleanup()
