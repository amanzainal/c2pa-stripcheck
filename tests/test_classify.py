"""Tests for the core classifier — the four verdicts plus invalid input."""

from __future__ import annotations

import pytest

from c2pa_stripcheck.classify import Verdict, classify
from c2pa_stripcheck.verify import ManifestInfo

SIGNER_A = "CN=Original Signer, O=demo, C=XX"
SIGNER_B = "CN=Platform Signer, O=other, C=XX"


def _signed(signer=SIGNER_A, gen="gen/1"):
    return ManifestInfo(present=True, signer=signer, claim_generator=gen)


def _absent():
    return ManifestInfo(present=False)


def test_preserved_same_signer():
    c = classify(_signed(), _signed())
    assert c.verdict is Verdict.PRESERVED


def test_stripped_when_manifest_gone_and_no_softbinding():
    c = classify(_signed(), _absent())
    assert c.verdict is Verdict.STRIPPED


def test_resigned_when_different_signer():
    c = classify(_signed(SIGNER_A), _signed(SIGNER_B))
    assert c.verdict is Verdict.RE_SIGNED
    assert c.signer_before == SIGNER_A
    assert c.signer_after == SIGNER_B


def test_soft_binding_recoverable_when_gone_but_watermark_survives():
    c = classify(_signed(), _absent(), soft_binding_id="wm-1")
    assert c.verdict is Verdict.SOFT_BINDING_RECOVERABLE
    assert c.soft_binding_id == "wm-1"


def test_absent_before_is_invalid_test():
    with pytest.raises(ValueError):
        classify(_absent(), _absent())


def test_resigned_falls_back_to_claim_generator_when_signer_unknown():
    before = ManifestInfo(present=True, signer=None, claim_generator="gen/A")
    after = ManifestInfo(present=True, signer=None, claim_generator="gen/B")
    assert classify(before, after).verdict is Verdict.RE_SIGNED


def test_preserved_when_both_opaque():
    # Builtin scanner on a real asset: presence known, details unknown.
    before = ManifestInfo(present=True, signer=None, claim_generator=None)
    after = ManifestInfo(present=True, signer=None, claim_generator=None)
    assert classify(before, after).verdict is Verdict.PRESERVED


def test_verdict_has_emoji_and_label_for_every_value():
    for v in Verdict:
        assert v.emoji
        assert v.label
