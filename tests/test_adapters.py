"""Tests for the adapter framework: mock behaviors and stub safety."""

from __future__ import annotations

import pytest

from c2pa_stripcheck import fixtures
from c2pa_stripcheck.adapters import (
    MockAdapter,
    MockBehavior,
    get_adapter,
    list_adapters,
    registry,
)
from c2pa_stripcheck.classify import Verdict
from c2pa_stripcheck.probe import run_probe


@pytest.fixture
def signed_asset(tmp_path):
    p = tmp_path / "signed.synthetic"
    p.write_bytes(fixtures.make_signed_bytes(soft_binding_id="wm-x"))
    return p


@pytest.mark.parametrize(
    "behavior,expected",
    [
        (MockBehavior.PRESERVE, Verdict.PRESERVED.value),
        (MockBehavior.STRIP, Verdict.STRIPPED.value),
        (MockBehavior.RESIGN, Verdict.RE_SIGNED.value),
        (MockBehavior.SOFT_BINDING, Verdict.SOFT_BINDING_RECOVERABLE.value),
    ],
)
def test_mock_adapter_produces_expected_verdict(
    behavior, expected, signed_asset, tmp_path
):
    adapter = MockAdapter(name="m", behavior=behavior)
    result = run_probe(adapter, signed_asset, tmp_path / "work")
    assert result.verdict == expected
    assert result.error is None


def test_stub_adapters_are_registered():
    reg = registry()
    # The spec names these platforms; all should be present as stubs.
    for name in ["instagram", "x", "whatsapp", "reddit", "tiktok", "linkedin"]:
        assert name in reg


def test_stub_adapter_probe_is_untested_not_fake(signed_asset, tmp_path):
    adapter = get_adapter("instagram")
    result = run_probe(adapter, signed_asset, tmp_path / "work")
    assert result.verdict == "UNTESTED"
    assert result.error is not None  # must surface why, never silently pass


def test_unknown_adapter_raises():
    with pytest.raises(KeyError):
        get_adapter("not-a-real-platform")


def test_list_adapters_describes_every_stub():
    described = list_adapters()
    assert len(described) == len(registry())
    for d in described:
        assert d["kind"] == "stub"
        assert d["requires_account"] is True
