"""Classify what a platform did to an asset's Content Credentials.

Given the manifest read from the ORIGINAL (uploaded) asset and the manifest read
from the RE-FETCHED (downloaded) asset, plus an optional soft-binding probe,
decide which of four outcomes occurred.

This module is the core of the tool and is pure / deterministic, so it is the
most heavily tested. It contains no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .verify import ManifestInfo


class Verdict(str, Enum):
    """The four behaviors a platform can exhibit toward Content Credentials."""

    PRESERVED = "PRESERVED"
    STRIPPED = "STRIPPED"
    RE_SIGNED = "RE-SIGNED"
    SOFT_BINDING_RECOVERABLE = "SOFT-BINDING-RECOVERABLE"

    @property
    def emoji(self) -> str:
        return {
            Verdict.PRESERVED: "✅",
            Verdict.STRIPPED: "❌",
            Verdict.RE_SIGNED: "🔁",
            Verdict.SOFT_BINDING_RECOVERABLE: "🔗",
        }[self]

    @property
    def label(self) -> str:
        return {
            Verdict.PRESERVED: "Preserved",
            Verdict.STRIPPED: "Stripped",
            Verdict.RE_SIGNED: "Re-signed",
            Verdict.SOFT_BINDING_RECOVERABLE: "Stripped, soft-binding recoverable",
        }[self]


@dataclass(frozen=True)
class Classification:
    verdict: Verdict
    reason: str
    # The signer string before/after, surfaced for the report.
    signer_before: str | None = None
    signer_after: str | None = None
    soft_binding_id: str | None = None


def classify(
    before: ManifestInfo,
    after: ManifestInfo,
    *,
    soft_binding_id: str | None = None,
) -> Classification:
    """Decide the verdict for one before/after pair.

    Logic, in priority order:

    * No manifest before -> the test is invalid; we raise. (Callers must upload a
      genuinely signed asset.)
    * Manifest still present after, same signer  -> PRESERVED.
    * Manifest still present after, DIFFERENT signer (or different claim
      generator) -> RE_SIGNED: the platform stripped the original and applied its
      own credentials.
    * Manifest gone after, but a soft-binding watermark survives ->
      SOFT_BINDING_RECOVERABLE: the C2PA bytes were removed, yet provenance can be
      recovered via TrustMark + the CAI Soft-Binding Resolution API.
    * Manifest gone after, nothing recoverable -> STRIPPED.
    """
    if before.absent:
        raise ValueError(
            "before-manifest is absent: the uploaded asset was not signed, so "
            "strip/preserve cannot be measured. Use a signed input or --demo."
        )

    if after.present:
        if _same_provenance(before, after):
            return Classification(
                verdict=Verdict.PRESERVED,
                reason="Re-fetched asset carries the same manifest signer/generator.",
                signer_before=before.signer,
                signer_after=after.signer,
                soft_binding_id=soft_binding_id,
            )
        return Classification(
            verdict=Verdict.RE_SIGNED,
            reason=(
                "Re-fetched asset carries a manifest from a different signer "
                "than was uploaded (platform replaced the credentials)."
            ),
            signer_before=before.signer,
            signer_after=after.signer,
            soft_binding_id=soft_binding_id,
        )

    # Manifest is gone after re-fetch.
    if soft_binding_id:
        return Classification(
            verdict=Verdict.SOFT_BINDING_RECOVERABLE,
            reason=(
                "Embedded manifest removed, but a TrustMark soft-binding "
                "watermark survived; provenance is recoverable via the CAI "
                "Soft-Binding Resolution API."
            ),
            signer_before=before.signer,
            signer_after=None,
            soft_binding_id=soft_binding_id,
        )

    return Classification(
        verdict=Verdict.STRIPPED,
        reason="Re-fetched asset carries no manifest and no recoverable soft binding.",
        signer_before=before.signer,
        signer_after=None,
        soft_binding_id=None,
    )


def _same_provenance(before: ManifestInfo, after: ManifestInfo) -> bool:
    """Heuristic for 'the original credentials survived intact'.

    We treat the manifest as preserved when the signer matches (when known). If
    the signer is unknown on both sides, fall back to claim_generator. If neither
    is known (e.g. builtin scanner on a real asset), presence-after is treated as
    preservation conservatively, because we cannot prove a re-sign.
    """
    if before.signer is not None and after.signer is not None:
        return before.signer == after.signer
    if before.claim_generator is not None and after.claim_generator is not None:
        return before.claim_generator == after.claim_generator
    # Both sides opaque: presence survived; assume preserved.
    return True
