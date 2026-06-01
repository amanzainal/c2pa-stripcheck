"""Offline mock adapter that simulates configurable platform behaviors.

It implements the full :class:`PlatformAdapter` contract without any network:
``upload`` just copies the bytes; ``refetch`` returns bytes transformed
according to a configured behavior. This lets the verify/classify/matrix/report
pipeline be tested end-to-end offline with deterministic, synthetic data.
"""

from __future__ import annotations

import shutil
from enum import Enum
from pathlib import Path

from .. import fixtures
from .base import PlatformAdapter, UploadHandle


class MockBehavior(str, Enum):
    """How the mock platform mangles an uploaded asset on re-fetch."""

    PRESERVE = "preserve"  # returns the manifest untouched
    STRIP = "strip"  # removes the manifest entirely
    RESIGN = "resign"  # replaces the manifest with the platform's own signer
    SOFT_BINDING = "soft-binding"  # strips manifest but keeps TrustMark watermark


class MockAdapter(PlatformAdapter):
    """A simulated platform with a configurable behavior."""

    kind = "mock"
    requires_account = False

    def __init__(
        self,
        name: str = "mock",
        display_name: str = "Mock Platform",
        behavior: MockBehavior = MockBehavior.STRIP,
        notes: str = "Simulated platform for offline tests.",
    ) -> None:
        self.name = name
        self.display_name = display_name
        self.behavior = MockBehavior(behavior)
        self.notes = notes

    def upload(self, asset_path: str | Path) -> UploadHandle:
        src = Path(asset_path)
        if not src.exists():
            raise FileNotFoundError(src)
        return UploadHandle(ref=str(src), meta={"behavior": self.behavior.value})

    def refetch(self, handle: UploadHandle, dest_dir: str | Path) -> Path:
        src = Path(handle.ref)
        out_dir = Path(dest_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / f"{self.name}_refetched.synthetic"

        if self.behavior is MockBehavior.PRESERVE:
            shutil.copyfile(src, out)
        elif self.behavior is MockBehavior.STRIP:
            out.write_bytes(fixtures.make_stripped_bytes())
        elif self.behavior is MockBehavior.RESIGN:
            out.write_bytes(fixtures.make_resigned_bytes())
        elif self.behavior is MockBehavior.SOFT_BINDING:
            # Strip the manifest but preserve the watermark from the original.
            from ..verify import extract_soft_binding

            wm = extract_soft_binding(src) or "demo-wm-001"
            out.write_bytes(fixtures.make_stripped_bytes(soft_binding_id=wm))
        return out
