"""Read / verify C2PA manifests from an asset.

Strategy (graceful degradation, all optional):

1. ``c2pa-python`` native reader  -- best fidelity, only if the optional
   ``[verify]`` extra is installed.
2. ``c2patool`` CLI               -- if the binary is on ``PATH``.
3. Built-in JUMBF scanner         -- always available, dependency-free. It does
   NOT cryptographically verify; it locates the C2PA JUMBF superbox and reads
   the lightweight sidecar header that this tool's *synthetic* fixtures embed so
   the classify/matrix/report pipeline is fully testable offline.

The returned :class:`ManifestInfo` is intentionally small and stable: the
classifier only needs "is a manifest present, and what claim_generator / signer
/ instance_id does it carry", not a full validated manifest store.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

# JUMBF / C2PA box markers. The C2PA superbox label is the ASCII string "c2pa".
# Real embedded manifests are wrapped in a JUMBF superbox whose description box
# carries this label; our synthetic fixtures reuse the same marker so the scanner
# exercises the real code path.
_C2PA_JUMBF_MARKER = b"jumbf\x00c2pa"
_C2PA_LABEL = b"c2pa"

# Synthetic fixtures embed a tiny JSON sidecar header bracketed by these
# sentinels so the offline scanner can recover claim_generator/signer/etc.
# without a real CBOR/COSE parser. Real assets never contain these sentinels,
# so on a real asset the scanner reports "manifest present, details unknown".
_SIDECAR_OPEN = b"<<<C2PA-STRIPCHECK-SYNTH"
_SIDECAR_CLOSE = b"C2PA-STRIPCHECK-SYNTH>>>"


@dataclass(frozen=True)
class ManifestInfo:
    """A small, stable view of whatever provenance an asset carries."""

    present: bool
    claim_generator: str | None = None
    signer: str | None = None
    instance_id: str | None = None
    # How the read was performed: "c2pa-python" | "c2patool" | "builtin-scanner".
    reader: str = "builtin-scanner"
    # True only when a real verifier confirmed the signature validates.
    validated: bool = False
    raw: dict = field(default_factory=dict)

    @property
    def absent(self) -> bool:
        return not self.present


def _read_with_c2pa_python(path: Path) -> ManifestInfo | None:
    try:
        import c2pa  # type: ignore
    except Exception:
        return None
    try:
        reader = c2pa.Reader.from_file(str(path))  # type: ignore[attr-defined]
        manifest_json = reader.json()
        data = json.loads(manifest_json)
    except Exception:
        # Library present but asset has no readable manifest.
        return ManifestInfo(present=False, reader="c2pa-python")
    active = data.get("active_manifest")
    manifests = data.get("manifests", {})
    m = manifests.get(active, {}) if active else {}
    return ManifestInfo(
        present=True,
        claim_generator=m.get("claim_generator"),
        signer=_extract_signer(m),
        instance_id=m.get("instance_id"),
        reader="c2pa-python",
        validated=True,
        raw=data,
    )


def _read_with_c2patool(path: Path) -> ManifestInfo | None:
    exe = shutil.which("c2patool")
    if not exe:
        return None
    try:
        out = subprocess.run(
            [exe, str(path), "--no-signing", "--detailed"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except Exception:
        return None
    if out.returncode != 0:
        # c2patool exits non-zero when no manifest is found.
        return ManifestInfo(present=False, reader="c2patool")
    try:
        data = json.loads(out.stdout)
    except json.JSONDecodeError:
        return ManifestInfo(present=False, reader="c2patool")
    active = data.get("active_manifest")
    manifests = data.get("manifests", {})
    m = manifests.get(active, {}) if active else {}
    return ManifestInfo(
        present=True,
        claim_generator=m.get("claim_generator"),
        signer=_extract_signer(m),
        instance_id=m.get("instance_id"),
        reader="c2patool",
        validated=True,
        raw=data,
    )


def _extract_signer(manifest: dict) -> str | None:
    sig = manifest.get("signature_info") or {}
    return sig.get("issuer") or sig.get("common_name")


def _read_with_builtin_scanner(path: Path) -> ManifestInfo:
    """Dependency-free scan for an embedded C2PA JUMBF superbox.

    Detects presence via the JUMBF "c2pa" marker, and recovers synthetic
    fixture metadata from the sidecar header if present.
    """
    blob = path.read_bytes()
    present = _C2PA_JUMBF_MARKER in blob or (
        _C2PA_LABEL in blob and _SIDECAR_OPEN in blob
    )
    if not present:
        return ManifestInfo(present=False, reader="builtin-scanner")

    claim_generator = signer = instance_id = None
    start = blob.find(_SIDECAR_OPEN)
    if start != -1:
        end = blob.find(_SIDECAR_CLOSE, start)
        if end != -1:
            payload = blob[start + len(_SIDECAR_OPEN) : end]
            try:
                meta = json.loads(payload.decode("utf-8"))
                claim_generator = meta.get("claim_generator")
                signer = meta.get("signer")
                instance_id = meta.get("instance_id")
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass

    return ManifestInfo(
        present=True,
        claim_generator=claim_generator,
        signer=signer,
        instance_id=instance_id,
        reader="builtin-scanner",
        validated=False,
    )


def read_manifest(path: str | Path) -> ManifestInfo:
    """Read provenance from ``path`` using the best available reader.

    Always returns a :class:`ManifestInfo`; never raises for a missing manifest.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)

    for reader in (_read_with_c2pa_python, _read_with_c2patool):
        info = reader(p)
        if info is not None:
            return info
    return _read_with_builtin_scanner(p)


def available_readers() -> list[str]:
    """Return which manifest readers are usable in this environment."""
    readers = ["builtin-scanner"]
    if shutil.which("c2patool"):
        readers.insert(0, "c2patool")
    try:
        import c2pa  # type: ignore  # noqa: F401

        readers.insert(0, "c2pa-python")
    except Exception:
        pass
    return readers


def extract_soft_binding(path: str | Path) -> str | None:
    """Return a soft-binding watermark id if the asset carries one, else None.

    Real recovery uses Adobe TrustMark + the CAI Soft-Binding Resolution API
    (this tool intentionally CONSUMES those, it does not reimplement watermark
    decoding). For offline testing, synthetic fixtures encode the watermark id
    with a recognizable sentinel so the classifier can detect recoverability.
    """
    blob = Path(path).read_bytes()
    m = re.search(rb"<<<TRUSTMARK-SOFT-BINDING:([A-Za-z0-9._\-]+)>>>", blob)
    if m:
        return m.group(1).decode("ascii")
    return None
