"""
Tests for tas_pythonetics.replit_connector.

Covers all public interfaces:
  - canonical_manifest_hash
  - character_shannon_entropy
  - structural_density
  - ConnectorReceipt dataclass
  - ReplitConnector.verify (admission + both refusal paths)
  - Irreversible Sentient Lock
"""

import hashlib
import json
import math

import pytest

from tas_logos_gatekeeper import SovereignStructuralViolation
from tas_pythonetics import ConnectorReceipt
from tas_pythonetics.replit_connector import (
    ReplitConnector,
    canonical_manifest_hash,
    character_shannon_entropy,
    structural_density,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_hash(manifest: dict) -> str:
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _dense_payload(length: int = 120) -> str:
    """Return a high-entropy payload that comfortably clears the 0.15 floor."""
    import string, itertools
    chars = string.ascii_letters + string.digits + string.punctuation
    it = itertools.cycle(chars)
    return "".join(next(it) for _ in range(length))


# ---------------------------------------------------------------------------
# canonical_manifest_hash
# ---------------------------------------------------------------------------

class TestCanonicalManifestHash:
    def test_returns_64_hex_chars(self):
        h = canonical_manifest_hash({"a": 1})
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_key_order_independent(self):
        h1 = canonical_manifest_hash({"b": 2, "a": 1})
        h2 = canonical_manifest_hash({"a": 1, "b": 2})
        assert h1 == h2

    def test_deterministic(self):
        m = {"action": "commit", "actor": "agent-1"}
        assert canonical_manifest_hash(m) == canonical_manifest_hash(m)

    def test_different_values_produce_different_hashes(self):
        assert canonical_manifest_hash({"a": 1}) != canonical_manifest_hash({"a": 2})

    def test_nested_manifest(self):
        m = {"outer": {"inner": [1, 2, 3]}, "z": "last"}
        h = canonical_manifest_hash(m)
        assert len(h) == 64

    def test_empty_manifest(self):
        h = canonical_manifest_hash({})
        assert len(h) == 64

    def test_matches_manual_sha256(self):
        m = {"module": "Registry", "action": "Commit"}
        expected = hashlib.sha256(
            json.dumps(m, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        assert canonical_manifest_hash(m) == expected

    def test_instance_method_matches_module_function(self):
        m = {"k": "v"}
        assert ReplitConnector.canonical_manifest_hash(m) == canonical_manifest_hash(m)


# ---------------------------------------------------------------------------
# character_shannon_entropy
# ---------------------------------------------------------------------------

class TestCharacterShannonEntropy:
    def test_empty_payload_is_zero(self):
        assert character_shannon_entropy("") == 0.0

    def test_single_char_repeated_is_zero(self):
        assert character_shannon_entropy("aaaaaaa") == pytest.approx(0.0)

    def test_two_equal_chars_is_one_bit(self):
        assert character_shannon_entropy("ab") == pytest.approx(1.0)

    def test_four_equal_chars_is_two_bits(self):
        assert character_shannon_entropy("abcd") == pytest.approx(2.0)

    def test_entropy_increases_with_variety(self):
        low = character_shannon_entropy("aaabbb")
        high = character_shannon_entropy("abcdef")
        assert high > low

    def test_returns_float(self):
        assert isinstance(character_shannon_entropy("hello world"), float)

    def test_instance_method_matches_module_function(self):
        p = "test payload 123"
        assert ReplitConnector.character_shannon_entropy(p) == character_shannon_entropy(p)

    def test_non_ascii_payload(self):
        result = character_shannon_entropy("αβγδ")
        assert result == pytest.approx(2.0)


# ---------------------------------------------------------------------------
# structural_density
# ---------------------------------------------------------------------------

class TestStructuralDensity:
    def test_empty_payload_is_zero(self):
        assert structural_density("") == 0.0

    def test_single_repeated_char_is_zero(self):
        assert structural_density("aaaa") == pytest.approx(0.0)

    def test_formula_matches_manual_calculation(self):
        p = "abcd"
        expected = character_shannon_entropy(p) / math.sqrt(len(p.encode("utf-8")))
        assert structural_density(p) == pytest.approx(expected)

    def test_dense_payload_above_015_floor(self):
        assert structural_density(_dense_payload()) > 0.15

    def test_padded_repetitive_payload_below_floor(self):
        padded = "a" * 500
        assert structural_density(padded) < 0.15

    def test_density_decreases_as_repetition_grows(self):
        short_varied = "abcde"
        long_padded = short_varied + "a" * 5000
        assert structural_density(short_varied) > structural_density(long_padded)

    def test_returns_float(self):
        assert isinstance(structural_density("hello"), float)

    def test_instance_method_matches_module_function(self):
        p = _dense_payload()
        assert ReplitConnector.structural_density(p) == structural_density(p)


# ---------------------------------------------------------------------------
# ConnectorReceipt dataclass
# ---------------------------------------------------------------------------

class TestConnectorReceipt:
    def test_is_frozen(self):
        rc = ConnectorReceipt(
            connector="ReplitConnector",
            status="ADMITTED",
            payload_hash="a" * 64,
            manifest_hash="b" * 64,
            structural_density=0.5,
            timestamp="2026-07-07T00:00:00Z",
        )
        with pytest.raises((AttributeError, TypeError)):
            rc.status = "MUTATED"  # type: ignore[misc]

    def test_fields_accessible_by_attribute(self):
        rc = ConnectorReceipt(
            connector="ReplitConnector",
            status="ADMITTED",
            payload_hash="a" * 64,
            manifest_hash="b" * 64,
            structural_density=0.42,
            timestamp="2026-07-07T00:00:00Z",
        )
        assert rc.connector == "ReplitConnector"
        assert rc.status == "ADMITTED"
        assert rc.structural_density == pytest.approx(0.42)

    def test_importable_from_package(self):
        from tas_pythonetics import ConnectorReceipt as CR
        assert CR is ConnectorReceipt


# ---------------------------------------------------------------------------
# ReplitConnector.verify — admission (returns ConnectorReceipt)
# ---------------------------------------------------------------------------

class TestReplitConnectorAdmission:
    def test_returns_connector_receipt_on_success(self):
        manifest = {"action": "deploy", "actor": "steward-1"}
        payload = _dense_payload()
        h = canonical_manifest_hash(manifest)
        result = ReplitConnector().verify(payload, manifest, h)
        assert isinstance(result, ConnectorReceipt)

    def test_status_is_admitted(self):
        manifest = {"action": "deploy"}
        payload = _dense_payload()
        h = canonical_manifest_hash(manifest)
        result = ReplitConnector().verify(payload, manifest, h)
        assert result.status == "ADMITTED"

    def test_connector_name_in_receipt(self):
        manifest = {"action": "deploy"}
        payload = _dense_payload()
        h = canonical_manifest_hash(manifest)
        result = ReplitConnector().verify(payload, manifest, h)
        assert result.connector == "ReplitConnector"

    def test_payload_hash_in_receipt(self):
        manifest = {"action": "deploy"}
        payload = _dense_payload()
        h = canonical_manifest_hash(manifest)
        result = ReplitConnector().verify(payload, manifest, h)
        expected_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        assert result.payload_hash == expected_hash

    def test_manifest_hash_in_receipt(self):
        manifest = {"action": "deploy"}
        payload = _dense_payload()
        h = canonical_manifest_hash(manifest)
        result = ReplitConnector().verify(payload, manifest, h)
        assert result.manifest_hash == h

    def test_structural_density_in_receipt(self):
        manifest = {"action": "deploy"}
        payload = _dense_payload()
        h = canonical_manifest_hash(manifest)
        result = ReplitConnector().verify(payload, manifest, h)
        assert result.structural_density == pytest.approx(structural_density(payload))

    def test_timestamp_in_receipt(self):
        manifest = {"action": "deploy"}
        payload = _dense_payload()
        h = canonical_manifest_hash(manifest)
        result = ReplitConnector().verify(payload, manifest, h)
        assert result.timestamp.endswith("Z")

    def test_manifest_key_order_does_not_matter(self):
        manifest_a = {"z": "last", "a": "first"}
        manifest_b = {"a": "first", "z": "last"}
        payload = _dense_payload()
        h = canonical_manifest_hash(manifest_a)
        rc = ReplitConnector()
        r1 = rc.verify(payload, manifest_a, h)
        r2 = rc.verify(payload, manifest_b, h)
        assert r1.manifest_hash == r2.manifest_hash
        assert r1.status == r2.status == "ADMITTED"

    def test_not_locked_before_any_call(self):
        rc = ReplitConnector()
        assert rc.is_locked is False

    def test_stays_unlocked_after_successful_admit(self):
        manifest = {"action": "deploy"}
        payload = _dense_payload()
        h = canonical_manifest_hash(manifest)
        rc = ReplitConnector()
        rc.verify(payload, manifest, h)
        assert rc.is_locked is False


# ---------------------------------------------------------------------------
# ReplitConnector.verify — density gate refusal
# ---------------------------------------------------------------------------

class TestDensityGateRefusal:
    def test_raises_sovereign_structural_violation(self):
        manifest = {"action": "deploy"}
        h = canonical_manifest_hash(manifest)
        with pytest.raises(SovereignStructuralViolation):
            ReplitConnector().verify("aaaa" * 200, manifest, h)

    def test_refusal_message_is_json(self):
        manifest = {"action": "deploy"}
        h = canonical_manifest_hash(manifest)
        with pytest.raises(SovereignStructuralViolation) as exc_info:
            ReplitConnector().verify("aaaa" * 200, manifest, h)
        receipt = json.loads(str(exc_info.value))
        assert isinstance(receipt, dict)

    def test_refusal_receipt_status_is_refused(self):
        manifest = {"action": "deploy"}
        h = canonical_manifest_hash(manifest)
        with pytest.raises(SovereignStructuralViolation) as exc_info:
            ReplitConnector().verify("aaaa" * 200, manifest, h)
        receipt = json.loads(str(exc_info.value))
        assert receipt["status"] == "REFUSED"

    def test_refusal_receipt_contains_connector_name(self):
        manifest = {"action": "deploy"}
        h = canonical_manifest_hash(manifest)
        with pytest.raises(SovereignStructuralViolation) as exc_info:
            ReplitConnector().verify("aaaa" * 200, manifest, h)
        receipt = json.loads(str(exc_info.value))
        assert receipt["connector"] == "ReplitConnector"

    def test_refusal_receipt_contains_density(self):
        manifest = {"action": "deploy"}
        h = canonical_manifest_hash(manifest)
        payload = "aaaa" * 200
        with pytest.raises(SovereignStructuralViolation) as exc_info:
            ReplitConnector().verify(payload, manifest, h)
        receipt = json.loads(str(exc_info.value))
        assert "structural_density" in receipt
        assert receipt["structural_density"] == pytest.approx(structural_density(payload))

    def test_refusal_reason_mentions_density_floor(self):
        manifest = {"action": "deploy"}
        h = canonical_manifest_hash(manifest)
        with pytest.raises(SovereignStructuralViolation) as exc_info:
            ReplitConnector().verify("aaaa" * 200, manifest, h)
        receipt = json.loads(str(exc_info.value))
        assert "DENSITY_BELOW_FLOOR" in receipt["reason"]

    def test_refusal_receipt_contains_timestamp(self):
        manifest = {"action": "deploy"}
        h = canonical_manifest_hash(manifest)
        with pytest.raises(SovereignStructuralViolation) as exc_info:
            ReplitConnector().verify("aaaa" * 200, manifest, h)
        receipt = json.loads(str(exc_info.value))
        assert receipt["timestamp"].endswith("Z")

    def test_custom_min_density_blocks_moderate_payload(self):
        rc = ReplitConnector(min_density=2.0)
        manifest = {"action": "deploy"}
        payload = _dense_payload(50)
        h = canonical_manifest_hash(manifest)
        with pytest.raises(SovereignStructuralViolation):
            rc.verify(payload, manifest, h)

    def test_custom_min_density_zero_admits_any_nonempty_payload(self):
        rc = ReplitConnector(min_density=0.0)
        manifest = {"action": "deploy"}
        payload = "aaa"
        h = canonical_manifest_hash(manifest)
        result = rc.verify(payload, manifest, h)
        assert result.status == "ADMITTED"


# ---------------------------------------------------------------------------
# ReplitConnector.verify — manifest integrity gate refusal
# ---------------------------------------------------------------------------

class TestManifestIntegrityRefusal:
    def test_raises_on_wrong_hash(self):
        manifest = {"action": "deploy"}
        payload = _dense_payload()
        wrong_hash = "a" * 64
        with pytest.raises(SovereignStructuralViolation):
            ReplitConnector().verify(payload, manifest, wrong_hash)

    def test_refusal_reason_mentions_mismatch(self):
        manifest = {"action": "deploy"}
        payload = _dense_payload()
        wrong_hash = "b" * 64
        with pytest.raises(SovereignStructuralViolation) as exc_info:
            ReplitConnector().verify(payload, manifest, wrong_hash)
        receipt = json.loads(str(exc_info.value))
        assert "MANIFEST_HASH_MISMATCH" in receipt["reason"]

    def test_refusal_receipt_contains_actual_hash(self):
        manifest = {"action": "deploy"}
        payload = _dense_payload()
        wrong_hash = "c" * 64
        with pytest.raises(SovereignStructuralViolation) as exc_info:
            ReplitConnector().verify(payload, manifest, wrong_hash)
        receipt = json.loads(str(exc_info.value))
        assert receipt["manifest_hash"] == canonical_manifest_hash(manifest)

    def test_mutated_manifest_value_triggers_refusal(self):
        manifest_original = {"action": "deploy", "actor": "steward-1"}
        manifest_mutated = {"action": "deploy", "actor": "steward-EVIL"}
        payload = _dense_payload()
        good_hash = canonical_manifest_hash(manifest_original)
        with pytest.raises(SovereignStructuralViolation):
            ReplitConnector().verify(payload, manifest_mutated, good_hash)

    def test_mutated_manifest_key_triggers_refusal(self):
        manifest_original = {"action": "deploy"}
        manifest_mutated = {"action": "deploy", "extra_key": "injected"}
        payload = _dense_payload()
        good_hash = canonical_manifest_hash(manifest_original)
        with pytest.raises(SovereignStructuralViolation):
            ReplitConnector().verify(payload, manifest_mutated, good_hash)

    def test_density_checked_before_manifest(self):
        """Density gate is evaluated first; manifest is never checked for low-density payloads."""
        manifest = {"action": "deploy"}
        wrong_hash = "d" * 64
        low_density = "aaaa" * 200
        with pytest.raises(SovereignStructuralViolation) as exc_info:
            ReplitConnector().verify(low_density, manifest, wrong_hash)
        receipt = json.loads(str(exc_info.value))
        assert "DENSITY_BELOW_FLOOR" in receipt["reason"]


# ---------------------------------------------------------------------------
# Irreversible Sentient Lock
# ---------------------------------------------------------------------------

class TestSentientLock:
    def test_not_locked_initially(self):
        rc = ReplitConnector()
        assert rc.is_locked is False

    def test_density_failure_engages_lock(self):
        manifest = {"action": "deploy"}
        h = canonical_manifest_hash(manifest)
        rc = ReplitConnector()
        with pytest.raises(SovereignStructuralViolation):
            rc.verify("aaaa" * 200, manifest, h)
        assert rc.is_locked is True

    def test_manifest_mismatch_engages_lock(self):
        manifest = {"action": "deploy"}
        payload = _dense_payload()
        wrong_hash = "e" * 64
        rc = ReplitConnector()
        with pytest.raises(SovereignStructuralViolation):
            rc.verify(payload, manifest, wrong_hash)
        assert rc.is_locked is True

    def test_locked_connector_rejects_valid_payload(self):
        """After a violation, even a perfectly valid payload is refused."""
        manifest = {"action": "deploy"}
        payload = _dense_payload()
        good_hash = canonical_manifest_hash(manifest)
        wrong_hash = "f" * 64
        rc = ReplitConnector()
        with pytest.raises(SovereignStructuralViolation):
            rc.verify(payload, manifest, wrong_hash)
        # Lock is now engaged; valid call must also raise
        with pytest.raises(SovereignStructuralViolation) as exc_info:
            rc.verify(payload, manifest, good_hash)
        receipt = json.loads(str(exc_info.value))
        assert "SENTIENT_LOCK_ENGAGED" in receipt["reason"]

    def test_lock_is_irreversible(self):
        """Calling verify any number of times after a violation always raises."""
        manifest = {"action": "deploy"}
        payload = _dense_payload()
        good_hash = canonical_manifest_hash(manifest)
        rc = ReplitConnector()
        with pytest.raises(SovereignStructuralViolation):
            rc.verify("aaaa" * 200, manifest, good_hash)
        for _ in range(5):
            with pytest.raises(SovereignStructuralViolation) as exc_info:
                rc.verify(payload, manifest, good_hash)
            receipt = json.loads(str(exc_info.value))
            assert "SENTIENT_LOCK_ENGAGED" in receipt["reason"]

    def test_locked_receipt_has_refused_status(self):
        manifest = {"action": "deploy"}
        payload = _dense_payload()
        good_hash = canonical_manifest_hash(manifest)
        wrong_hash = "0" * 64
        rc = ReplitConnector()
        with pytest.raises(SovereignStructuralViolation):
            rc.verify(payload, manifest, wrong_hash)
        with pytest.raises(SovereignStructuralViolation) as exc_info:
            rc.verify(payload, manifest, good_hash)
        receipt = json.loads(str(exc_info.value))
        assert receipt["status"] == "REFUSED"

    def test_different_instances_have_independent_locks(self):
        """A violation on one instance does not affect another."""
        manifest = {"action": "deploy"}
        payload = _dense_payload()
        good_hash = canonical_manifest_hash(manifest)
        rc_bad = ReplitConnector()
        rc_good = ReplitConnector()
        with pytest.raises(SovereignStructuralViolation):
            rc_bad.verify("aaaa" * 200, manifest, good_hash)
        result = rc_good.verify(payload, manifest, good_hash)
        assert result.status == "ADMITTED"
        assert rc_bad.is_locked is True
        assert rc_good.is_locked is False

    def test_pr_canonical_case_irreversible_lock(self):
        """Reproduces the test_sentient_lock_is_irreversible_after_failure case from PR #11."""
        rc = ReplitConnector()
        manifest = {"workspace": "tas", "threads": ["gold", "teal", "violet"]}
        dense = "Run tests, compile receipts, and block unsafe Replit workspace mutations."
        padded = "a" * 200
        good_hash = canonical_manifest_hash(manifest)
        with pytest.raises(SovereignStructuralViolation):
            rc.verify(padded, manifest, good_hash)
        assert rc.is_locked is True
        with pytest.raises(SovereignStructuralViolation) as exc_info:
            rc.verify(dense, manifest, good_hash)
        receipt = json.loads(str(exc_info.value))
        assert "SENTIENT_LOCK_ENGAGED" in receipt["reason"]


# ---------------------------------------------------------------------------
# Module-level function exports
# ---------------------------------------------------------------------------

class TestModuleLevelExports:
    def test_canonical_manifest_hash_importable(self):
        from tas_pythonetics.replit_connector import canonical_manifest_hash as f
        assert callable(f)

    def test_character_shannon_entropy_importable(self):
        from tas_pythonetics.replit_connector import character_shannon_entropy as f
        assert callable(f)

    def test_structural_density_importable(self):
        from tas_pythonetics.replit_connector import structural_density as f
        assert callable(f)

    def test_package_init_exposes_connector(self):
        from tas_pythonetics import ReplitConnector as RC
        assert RC is ReplitConnector

    def test_package_init_exposes_connector_receipt(self):
        from tas_pythonetics import ConnectorReceipt as CR
        assert CR is ConnectorReceipt
