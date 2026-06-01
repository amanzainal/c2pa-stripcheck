"""The declarative platform-probe contract.

Each platform is an *adapter* describing three things:

  * ``upload(asset_path) -> handle``       send the signed asset to the platform
  * ``refetch(handle) -> downloaded_path`` pull the platform's processed copy back
  * (classification is done by the shared classifier, not the adapter)

Real adapters need accounts/credentials and live network access, so in this v0
they are clearly-marked STUBS that raise :class:`NotImplementedError` with a
pointer to CONTRIBUTING.md. The MOCK adapter implements the full contract
against synthetic fixtures so the pipeline is exercised offline.

The crowd-maintained matrix IS the community value: contributors fill in real
adapters (or simply record observed behavior) over time.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class UploadHandle:
    """Opaque reference to an uploaded asset, returned by ``upload``.

    ``ref`` is whatever the adapter needs to re-fetch (a URL, post id, etc.).
    ``meta`` carries adapter-specific extras for the report.
    """

    ref: str
    meta: dict = field(default_factory=dict)


class PlatformAdapter(abc.ABC):
    """Base class for all platform probes."""

    #: Stable machine name, e.g. "instagram". Used as the matrix row key.
    name: str = ""
    #: Human-friendly display name, e.g. "Instagram".
    display_name: str = ""
    #: "mock" for the offline adapter, "stub" for unimplemented real adapters,
    #: "live" once a contributor wires up real upload/refetch.
    kind: str = "stub"
    #: Whether driving this adapter requires real credentials / network.
    requires_account: bool = True
    #: Free-form note shown in the report (e.g. "uploads via Graph API").
    notes: str = ""

    @abc.abstractmethod
    def upload(self, asset_path: str | Path) -> UploadHandle:
        """Upload ``asset_path`` to the platform; return a handle to re-fetch it."""

    @abc.abstractmethod
    def refetch(self, handle: UploadHandle, dest_dir: str | Path) -> Path:
        """Download the platform's processed copy into ``dest_dir``; return path."""

    def describe(self) -> dict:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "kind": self.kind,
            "requires_account": self.requires_account,
            "notes": self.notes,
        }


class StubAdapter(PlatformAdapter):
    """A real platform that is not yet wired up.

    Calling ``upload``/``refetch`` raises with a clear pointer to CONTRIBUTING.md
    so it never silently produces a fake result.
    """

    kind = "stub"

    def upload(self, asset_path: str | Path) -> UploadHandle:
        raise NotImplementedError(
            f"The '{self.name}' adapter is a stub. Implement upload()/refetch() "
            f"with real credentials, or record observed behavior in the matrix. "
            f"See CONTRIBUTING.md."
        )

    def refetch(self, handle: UploadHandle, dest_dir: str | Path) -> Path:
        raise NotImplementedError(
            f"The '{self.name}' adapter is a stub. See CONTRIBUTING.md."
        )
