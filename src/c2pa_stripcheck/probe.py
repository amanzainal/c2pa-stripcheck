"""Run a single platform probe end-to-end.

upload -> refetch -> read before/after manifests -> detect soft binding ->
classify. Produces a :class:`ProbeResult` that the runner aggregates into the
matrix.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import asdict, dataclass
from pathlib import Path

from .adapters.base import PlatformAdapter
from .classify import Classification, classify
from .verify import ManifestInfo, extract_soft_binding, read_manifest


@dataclass(frozen=True)
class ProbeResult:
    platform: str
    display_name: str
    kind: str
    verdict: str
    reason: str
    reader: str
    signer_before: str | None
    signer_after: str | None
    soft_binding_id: str | None
    tested_at: str
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


def run_probe(
    adapter: PlatformAdapter,
    signed_asset: str | Path,
    work_dir: str | Path,
) -> ProbeResult:
    """Probe one platform with a signed asset; never raises (errors captured)."""
    signed_asset = Path(signed_asset)
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    before = read_manifest(signed_asset)
    try:
        handle = adapter.upload(signed_asset)
        downloaded = adapter.refetch(handle, work_dir)
        after: ManifestInfo = read_manifest(downloaded)
        soft = extract_soft_binding(downloaded)
        result: Classification = classify(before, after, soft_binding_id=soft)
        return ProbeResult(
            platform=adapter.name,
            display_name=adapter.display_name or adapter.name,
            kind=adapter.kind,
            verdict=result.verdict.value,
            reason=result.reason,
            reader=after.reader,
            signer_before=result.signer_before,
            signer_after=result.signer_after,
            soft_binding_id=result.soft_binding_id,
            tested_at=_now_iso(),
        )
    except NotImplementedError as exc:
        return ProbeResult(
            platform=adapter.name,
            display_name=adapter.display_name or adapter.name,
            kind=adapter.kind,
            verdict="UNTESTED",
            reason="Adapter is a stub; no live result.",
            reader=before.reader,
            signer_before=before.signer,
            signer_after=None,
            soft_binding_id=None,
            tested_at=_now_iso(),
            error=str(exc),
        )
    except Exception as exc:  # pragma: no cover - defensive
        return ProbeResult(
            platform=adapter.name,
            display_name=adapter.display_name or adapter.name,
            kind=adapter.kind,
            verdict="ERROR",
            reason="Probe failed.",
            reader=before.reader,
            signer_before=before.signer,
            signer_after=None,
            soft_binding_id=None,
            tested_at=_now_iso(),
            error=f"{type(exc).__name__}: {exc}",
        )
