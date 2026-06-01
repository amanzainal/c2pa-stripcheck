"""Tests for the manifest reader / builtin scanner against synthetic fixtures."""

from __future__ import annotations

from c2pa_stripcheck import fixtures
from c2pa_stripcheck.verify import (
    available_readers,
    extract_soft_binding,
    read_manifest,
)


def test_signed_fixture_is_detected(tmp_path):
    p = tmp_path / "signed.synthetic"
    p.write_bytes(fixtures.make_signed_bytes())
    info = read_manifest(p)
    assert info.present is True
    assert info.absent is False
    assert info.signer == fixtures.DEFAULT_SIGNER
    assert info.claim_generator == fixtures.DEFAULT_CLAIM_GENERATOR
    assert info.instance_id == fixtures.DEFAULT_INSTANCE_ID
    # Builtin scanner never claims cryptographic validation.
    assert info.validated is False


def test_stripped_fixture_has_no_manifest(tmp_path):
    p = tmp_path / "stripped.synthetic"
    p.write_bytes(fixtures.make_stripped_bytes())
    info = read_manifest(p)
    assert info.present is False
    assert info.absent is True
    assert info.signer is None


def test_resigned_fixture_has_different_signer(tmp_path):
    p = tmp_path / "resigned.synthetic"
    p.write_bytes(fixtures.make_resigned_bytes())
    info = read_manifest(p)
    assert info.present is True
    assert info.signer != fixtures.DEFAULT_SIGNER


def test_soft_binding_extraction(tmp_path):
    p = tmp_path / "wm.synthetic"
    p.write_bytes(fixtures.make_stripped_bytes(soft_binding_id="abc-123"))
    assert extract_soft_binding(p) == "abc-123"


def test_no_soft_binding_returns_none(tmp_path):
    p = tmp_path / "plain.synthetic"
    p.write_bytes(fixtures.make_stripped_bytes())
    assert extract_soft_binding(p) is None


def test_signed_with_soft_binding_carries_both(tmp_path):
    p = tmp_path / "both.synthetic"
    p.write_bytes(fixtures.make_signed_bytes(soft_binding_id="wm-9"))
    info = read_manifest(p)
    assert info.present is True
    assert extract_soft_binding(p) == "wm-9"


def test_missing_file_raises(tmp_path):
    import pytest

    with pytest.raises(FileNotFoundError):
        read_manifest(tmp_path / "does-not-exist")


def test_available_readers_always_includes_builtin():
    assert "builtin-scanner" in available_readers()
