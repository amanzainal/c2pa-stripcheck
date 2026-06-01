"""Synthetic, obviously-fake fixture assets for offline testing.

These are NOT real images and NOT real C2PA manifests. They are tiny byte blobs
that the built-in scanner (see :mod:`verify`) recognizes, so the entire
verify -> classify -> matrix -> report pipeline runs with no network, no
accounts, and no GPU.

A "signed" fixture is a minimal byte container with:
  * a JUMBF "c2pa" superbox marker, and
  * a sidecar JSON header (claim_generator / signer / instance_id) bracketed by
    the stripcheck sentinels, and
  * optionally a TrustMark soft-binding sentinel.

A "stripped" fixture is the same container with all of that removed.

Everything here is deliberately synthetic. There are no real faces, people, or
copyrighted media anywhere in this repo.
"""

from __future__ import annotations

import json
from pathlib import Path

from .verify import (
    _C2PA_JUMBF_MARKER,
    _SIDECAR_CLOSE,
    _SIDECAR_OPEN,
)

# A clearly-fake "image" preamble so the bytes look like a synthetic container
# and never resemble a real photo of a person.
_FAKE_CONTAINER_PREAMBLE = (
    b"SYNTHETIC-C2PA-STRIPCHECK-FIXTURE\n"
    b"This is not a real image or a real C2PA manifest.\n"
)

DEFAULT_CLAIM_GENERATOR = "stripcheck-synth/0.1 (demo signer)"
DEFAULT_SIGNER = "CN=Synthetic Demo Signer, O=stripcheck, C=XX"
DEFAULT_INSTANCE_ID = "xmp:iid:synthetic-0000-demo"


def _sidecar(claim_generator: str, signer: str, instance_id: str) -> bytes:
    meta = {
        "claim_generator": claim_generator,
        "signer": signer,
        "instance_id": instance_id,
    }
    return _SIDECAR_OPEN + json.dumps(meta).encode("utf-8") + _SIDECAR_CLOSE


def make_signed_bytes(
    *,
    claim_generator: str = DEFAULT_CLAIM_GENERATOR,
    signer: str = DEFAULT_SIGNER,
    instance_id: str = DEFAULT_INSTANCE_ID,
    soft_binding_id: str | None = None,
) -> bytes:
    """Build the bytes of a synthetic *signed* asset."""
    parts = [
        _FAKE_CONTAINER_PREAMBLE,
        _C2PA_JUMBF_MARKER,
        _sidecar(claim_generator, signer, instance_id),
    ]
    if soft_binding_id:
        parts.append(
            b"<<<TRUSTMARK-SOFT-BINDING:" + soft_binding_id.encode("ascii") + b">>>"
        )
    return b"".join(parts)


def make_stripped_bytes(*, soft_binding_id: str | None = None) -> bytes:
    """Build the bytes of a synthetic *stripped* asset (no manifest).

    If ``soft_binding_id`` is given, the embedded C2PA manifest is gone but the
    TrustMark watermark survives (the SOFT-BINDING-RECOVERABLE case).
    """
    parts = [_FAKE_CONTAINER_PREAMBLE, b"NO-MANIFEST-PRESENT\n"]
    if soft_binding_id:
        parts.append(
            b"<<<TRUSTMARK-SOFT-BINDING:" + soft_binding_id.encode("ascii") + b">>>"
        )
    return b"".join(parts)


def make_resigned_bytes(
    *,
    claim_generator: str = "platform-pipeline/2.0",
    signer: str = "CN=Platform Re-Signer, O=ExamplePlatform, C=XX",
    instance_id: str = "xmp:iid:platform-resigned-0001",
) -> bytes:
    """Build a synthetic asset re-signed by a *different* signer."""
    return make_signed_bytes(
        claim_generator=claim_generator,
        signer=signer,
        instance_id=instance_id,
    )


def write_demo_fixtures(dest: str | Path) -> dict[str, Path]:
    """Write the canonical demo fixtures into ``dest`` and return their paths."""
    d = Path(dest)
    d.mkdir(parents=True, exist_ok=True)
    paths = {
        "signed": d / "signed_sample.synthetic",
        "stripped": d / "stripped_sample.synthetic",
        "resigned": d / "resigned_sample.synthetic",
        "soft_binding": d / "stripped_with_softbinding.synthetic",
    }
    paths["signed"].write_bytes(make_signed_bytes(soft_binding_id="demo-wm-001"))
    paths["stripped"].write_bytes(make_stripped_bytes())
    paths["resigned"].write_bytes(make_resigned_bytes())
    paths["soft_binding"].write_bytes(
        make_stripped_bytes(soft_binding_id="demo-wm-001")
    )
    return paths
