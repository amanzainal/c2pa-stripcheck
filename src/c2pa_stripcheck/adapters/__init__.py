"""Adapter registry.

Lists every known platform adapter. Real ones are stubs until contributors wire
them up; the mock adapter is always available for offline testing.
"""

from __future__ import annotations

from .base import PlatformAdapter, StubAdapter, UploadHandle
from .mock import MockAdapter, MockBehavior
from .stubs import STUB_ADAPTERS

__all__ = [
    "PlatformAdapter",
    "StubAdapter",
    "UploadHandle",
    "MockAdapter",
    "MockBehavior",
    "registry",
    "get_adapter",
    "list_adapters",
]


def registry() -> dict[str, type[PlatformAdapter]]:
    """Map of platform name -> adapter class for all real (stub) platforms."""
    return {cls.name: cls for cls in STUB_ADAPTERS}


def list_adapters() -> list[dict]:
    """Describe every registered real adapter (for ``list`` / docs)."""
    return [cls().describe() for cls in STUB_ADAPTERS]


def get_adapter(name: str) -> PlatformAdapter:
    """Instantiate a registered real adapter by name."""
    reg = registry()
    if name not in reg:
        raise KeyError(
            f"unknown platform '{name}'. Known: {', '.join(sorted(reg))}"
        )
    return reg[name]()
