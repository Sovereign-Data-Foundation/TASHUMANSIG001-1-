"""Tests for LedgerVerifier — ArtifactGuard ledger tamper-evidence hardening.

Covers:
- LedgerSeal: HMAC protection over the full ledger file (X3/W1).
- LedgerMerkle: rolling Merkle accumulator with cross-restart integrity.
"""
# © 2025 Russell Nordland | TrueAlphaSpiral (TAS) | Apache-2.0

import sys
import os
import json
import pathlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from ledger_verifier import LedgerSeal, LedgerMerkle, LedgerTampered


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _seal(tmp_path: pathlib.Path, **kwargs) -> LedgerSeal:
    ledger = tmp_path / "artifacts.hash"
    seal = tmp_path / "artifacts.seal"
    return LedgerSeal(ledger_path=ledger, seal_path=seal, **kwargs)


def _merkle(tmp_path: pathlib.Path, **kwargs) -> LedgerMerkle:
    ledger = tmp_path / "artifacts.hash"
    merkle = tmp_path / "artifacts.merkle"
    return LedgerMerkle(ledger_path=ledger, merkle_path=merkle, **kwargs)


# ===========================================================================
# TestLedgerSeal — HMAC integrity
# ===========================================================================


class TestLedgerSeal:
    """Invariant X3/W1 — LedgerSeal HMAC tamper detection.

    The ledger HMAC seal must detect any modification to the ledger file
    that bypasses the normal ``record()`` API.
    """

    def test_empty_ledger_verifies(self, tmp_path):
        s = _seal(tmp_path)
        assert s.verify()

    def test_single_record_verifies(self, tmp_path):
        s = _seal(tmp_path)
        s.record("abc123  artifact-001.json  wake=deadbeef")
        assert s.verify()

    def test_multiple_records_verify(self, tmp_path):
        s = _seal(tmp_path)
        for i in range(10):
            s.record(f"digest{i:02d}  artifact-{i:03d}.json  wake=head{i}")
        assert s.verify()

    def test_tampered_ledger_detected(self, tmp_path):
        s = _seal(tmp_path)
        s.record("abc123  artifact-001.json  wake=deadbeef")
        ledger = tmp_path / "artifacts.hash"
        ledger.write_text(ledger.read_text() + "INJECTED\n")
        assert not s.verify()

    def test_assert_integrity_raises_on_tamper(self, tmp_path):
        s = _seal(tmp_path)
        s.record("abc123  artifact-001.json  wake=deadbeef")
        ledger = tmp_path / "artifacts.hash"
        ledger.write_text("tampered content\n")
        with pytest.raises(LedgerTampered):
            s.assert_integrity()

    def test_modified_seal_file_detected(self, tmp_path):
        s = _seal(tmp_path)
        s.record("abc123  artifact-001.json  wake=deadbeef")
        seal = tmp_path / "artifacts.seal"
        data = json.loads(seal.read_text())
        data["__hmac__"] = "0" * 64
        seal.write_text(json.dumps(data))
        assert not s.verify()

    def test_deleted_line_detected(self, tmp_path):
        s = _seal(tmp_path)
        s.record("line1  artifact-001.json  wake=head1")
        s.record("line2  artifact-002.json  wake=head2")
        ledger = tmp_path / "artifacts.hash"
        lines = ledger.read_text().splitlines()
        ledger.write_text(lines[0] + "\n")  # remove second line
        assert not s.verify()

    def test_custom_key_round_trips(self, tmp_path):
        key = b"Z" * 32
        s1 = _seal(tmp_path, integrity_key=key)
        s1.record("abc123  artifact-001.json  wake=deadbeef")
        s2 = LedgerSeal(
            ledger_path=tmp_path / "artifacts.hash",
            seal_path=tmp_path / "artifacts.seal",
            integrity_key=key,
        )
        assert s2.verify()

    def test_assert_integrity_passes_on_valid(self, tmp_path):
        s = _seal(tmp_path)
        s.record("abc123  artifact-001.json  wake=deadbeef")
        s.assert_integrity()  # must not raise


# ===========================================================================
# TestLedgerMerkle — Merkle accumulator
# ===========================================================================


class TestLedgerMerkle:
    """Invariant X3 — LedgerMerkle rolling Merkle root accumulator.

    The Merkle root must extend correctly with each line, detect retroactive
    tampering, and survive process restarts.
    """

    def test_initial_root_is_genesis(self, tmp_path):
        m = _merkle(tmp_path)
        assert m.root == bytes(32)
        assert m.count == 0

    def test_extend_changes_root(self, tmp_path):
        m = _merkle(tmp_path)
        r0 = m.root
        m.extend("line1")
        assert m.root != r0

    def test_extend_is_deterministic(self, tmp_path):
        m1 = _merkle(tmp_path)
        m2 = LedgerMerkle(
            ledger_path=tmp_path / "artifacts2.hash",
            merkle_path=tmp_path / "artifacts2.merkle",
        )
        lines = ["line-a", "line-b", "line-c"]
        for ln in lines:
            r1 = m1.extend(ln)
        for ln in lines:
            r2 = m2.extend(ln)
        assert r1 == r2

    def test_count_increments(self, tmp_path):
        m = _merkle(tmp_path)
        for i in range(5):
            m.extend(f"line-{i}")
        assert m.count == 5

    def test_root_hex_is_64_chars(self, tmp_path):
        m = _merkle(tmp_path)
        m.extend("line1")
        assert len(m.root_hex) == 64
        assert m.root_hex == m.root_hex.lower()

    def test_verify_against_empty_ledger(self, tmp_path):
        m = _merkle(tmp_path)
        assert m.verify_against_ledger()

    def test_verify_against_ledger_after_sync(self, tmp_path):
        ledger = tmp_path / "artifacts.hash"
        merkle = tmp_path / "artifacts.merkle"
        m = LedgerMerkle(ledger_path=ledger, merkle_path=merkle)
        lines = ["a  art1.json  wake=h1", "b  art2.json  wake=h2"]
        for ln in lines:
            ledger.open("a").write(ln + "\n")
            m.extend(ln)
        assert m.verify_against_ledger()

    def test_tampered_ledger_fails_verify(self, tmp_path):
        ledger = tmp_path / "artifacts.hash"
        merkle = tmp_path / "artifacts.merkle"
        m = LedgerMerkle(ledger_path=ledger, merkle_path=merkle)
        line = "abc  art1.json  wake=h1"
        ledger.open("a").write(line + "\n")
        m.extend(line)
        ledger.write_text("tampered line\n")
        assert not m.verify_against_ledger()

    def test_deleted_line_fails_verify(self, tmp_path):
        ledger = tmp_path / "artifacts.hash"
        merkle = tmp_path / "artifacts.merkle"
        m = LedgerMerkle(ledger_path=ledger, merkle_path=merkle)
        for i in range(3):
            ln = f"d{i}  art{i}.json  wake=h{i}"
            ledger.open("a").write(ln + "\n")
            m.extend(ln)
        # Remove the last line
        content = ledger.read_text().splitlines()
        ledger.write_text("\n".join(content[:-1]) + "\n")
        assert not m.verify_against_ledger()

    def test_inclusion_proof_found(self, tmp_path):
        ledger = tmp_path / "artifacts.hash"
        merkle = tmp_path / "artifacts.merkle"
        m = LedgerMerkle(ledger_path=ledger, merkle_path=merkle)
        line = "abc  art1.json  wake=h1"
        ledger.open("a").write(line + "\n")
        m.extend(line)
        assert m.inclusion_proof(line)

    def test_inclusion_proof_not_found(self, tmp_path):
        m = _merkle(tmp_path)
        assert not m.inclusion_proof("nonexistent line")

    def test_persistence_across_restart(self, tmp_path):
        ledger = tmp_path / "artifacts.hash"
        merkle = tmp_path / "artifacts.merkle"
        m1 = LedgerMerkle(ledger_path=ledger, merkle_path=merkle)
        for i in range(4):
            m1.extend(f"line-{i}")
        root_after = m1.root
        count_after = m1.count

        m2 = LedgerMerkle(ledger_path=ledger, merkle_path=merkle)
        assert m2.root == root_after
        assert m2.count == count_after

    def test_tampered_merkle_state_raises(self, tmp_path):
        ledger = tmp_path / "artifacts.hash"
        merkle = tmp_path / "artifacts.merkle"
        m1 = LedgerMerkle(ledger_path=ledger, merkle_path=merkle)
        m1.extend("line1")

        data = json.loads(merkle.read_text())
        data["__hmac__"] = "0" * 64
        merkle.write_text(json.dumps(data))

        with pytest.raises(LedgerTampered):
            LedgerMerkle(ledger_path=ledger, merkle_path=merkle)


# ===========================================================================
# TestLedgerSealAndMerkleComposed — joint hardening
# ===========================================================================


class TestLedgerSealAndMerkleComposed:
    """Both hardening layers compose correctly over the same ledger file."""

    def test_combined_record_and_verify(self, tmp_path):
        ledger = tmp_path / "artifacts.hash"
        seal = _seal(tmp_path)
        m = LedgerMerkle(
            ledger_path=ledger,
            merkle_path=tmp_path / "artifacts.merkle",
        )

        lines = [
            "d001  art001.json  wake=h001",
            "d002  art002.json  wake=h002",
            "d003  art003.json  wake=h003",
        ]
        for ln in lines:
            seal.record(ln)
            m.extend(ln)

        assert seal.verify()
        assert m.verify_against_ledger()

    def test_tamper_detected_by_both_layers(self, tmp_path):
        ledger = tmp_path / "artifacts.hash"
        seal = _seal(tmp_path)
        m = LedgerMerkle(
            ledger_path=ledger,
            merkle_path=tmp_path / "artifacts.merkle",
        )
        seal.record("d001  art001.json  wake=h001")
        m.extend("d001  art001.json  wake=h001")

        ledger.write_text("injected line\n")
        assert not seal.verify()
        assert not m.verify_against_ledger()
