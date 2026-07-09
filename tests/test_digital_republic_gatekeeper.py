"""
Tests for digital_republic.DigitalRepublicGatekeeper.

Verifies the four enforcement invariants from the Digital Republic Doctrine:
  1. Tier 0 Human Seed gate
  2. Geometric Bound (r=2.4) gate
  3. Admissible state evolution
  4. Receipt structure and commitment determinism

STAMP_ANCHOR_2026_07_07
"""

import hashlib
import json

import pytest

from digital_republic import DigitalRepublicGatekeeper


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def gk() -> DigitalRepublicGatekeeper:
    return DigitalRepublicGatekeeper()


@pytest.fixture
def valid_attestation():
    return {"valid": True, "nullifier": "0x8bfae3927f4c93a8b2c1e0f95d86ba73c4d5e6f2"}


@pytest.fixture
def payload():
    return {"module": "Registry_State_Transition", "action": "Commit_State"}


# ---------------------------------------------------------------------------
# Gate 1 — Tier 0 Human Seed invariant
# ---------------------------------------------------------------------------

class TestTierZeroHumanSeedGate:
    """Tier 0: no state transition may proceed without valid human attestation."""

    def test_none_attestation_is_refused(self, gk, payload):
        receipt = gk.verify_state_transition(
            x_current=0.4, r_parameter=2.0,
            steward_attestation=None, payload_data=payload
        )
        assert receipt["execution_status"].startswith("HALTED_AND_VISIBLE")
        assert "CRITICAL_SIGNATURE_FAILURE" in receipt["execution_status"]

    def test_empty_dict_attestation_is_refused(self, gk, payload):
        receipt = gk.verify_state_transition(
            x_current=0.4, r_parameter=2.0,
            steward_attestation={}, payload_data=payload
        )
        assert receipt["execution_status"].startswith("HALTED_AND_VISIBLE")
        assert "CRITICAL_SIGNATURE_FAILURE" in receipt["execution_status"]

    def test_valid_false_attestation_is_refused(self, gk, payload):
        receipt = gk.verify_state_transition(
            x_current=0.4, r_parameter=2.0,
            steward_attestation={"valid": False, "nullifier": "0xdeadbeef"},
            payload_data=payload,
        )
        assert receipt["execution_status"].startswith("HALTED_AND_VISIBLE")
        assert "CRITICAL_SIGNATURE_FAILURE" in receipt["execution_status"]

    def test_missing_valid_key_is_refused(self, gk, payload):
        receipt = gk.verify_state_transition(
            x_current=0.4, r_parameter=2.0,
            steward_attestation={"nullifier": "0xabc123"},
            payload_data=payload,
        )
        assert receipt["execution_status"].startswith("HALTED_AND_VISIBLE")

    def test_tier0_refusal_forces_inert_state(self, gk, payload):
        receipt = gk.verify_state_transition(
            x_current=0.4, r_parameter=2.0,
            steward_attestation=None, payload_data=payload
        )
        assert receipt["trajectory_metrics"]["resulting_state"] == pytest.approx(
            gk.inert_target, abs=1e-6
        )

    def test_tier0_refusal_zeroes_nullifier(self, gk, payload):
        receipt = gk.verify_state_transition(
            x_current=0.4, r_parameter=2.0,
            steward_attestation=None, payload_data=payload
        )
        assert receipt["steward_signature_nullifier"] == "0x" + "0" * 40

    def test_tier0_refusal_marks_breach(self, gk, payload):
        receipt = gk.verify_state_transition(
            x_current=0.4, r_parameter=2.0,
            steward_attestation=None, payload_data=payload
        )
        assert receipt["error_telemetry"]["admissibility_breach"] is True

    def test_tier0_refusal_receipt_code_contains_reason(self, gk, payload):
        receipt = gk.verify_state_transition(
            x_current=0.4, r_parameter=2.0,
            steward_attestation=None, payload_data=payload
        )
        assert "Missing_or_Invalid_Tier_0" in receipt["error_telemetry"]["receipt_code"]


# ---------------------------------------------------------------------------
# Gate 2 — Geometric Bound (r=2.4) invariant
# ---------------------------------------------------------------------------

class TestGeometricBoundGate:
    """Trajectories with r > 2.4 are cryptographically inadmissible."""

    def test_r_exactly_at_limit_is_admissible(self, gk, valid_attestation, payload):
        receipt = gk.verify_state_transition(
            x_current=0.4, r_parameter=2.4,
            steward_attestation=valid_attestation, payload_data=payload
        )
        assert receipt["execution_status"] == "ADMISSIBLE_AND_SEALED"

    def test_r_just_above_limit_is_halted(self, gk, valid_attestation, payload):
        receipt = gk.verify_state_transition(
            x_current=0.4, r_parameter=2.401,
            steward_attestation=valid_attestation, payload_data=payload
        )
        assert "TORQUE_STALL_TRIGGERED" in receipt["execution_status"]

    def test_r_3_1_is_halted(self, gk, valid_attestation, payload):
        receipt = gk.verify_state_transition(
            x_current=0.4, r_parameter=3.1,
            steward_attestation=valid_attestation, payload_data=payload
        )
        assert receipt["execution_status"].startswith("HALTED_AND_VISIBLE")
        assert "TORQUE_STALL_TRIGGERED" in receipt["execution_status"]

    def test_chaotic_r_forces_banach_inert_state(self, gk, valid_attestation, payload):
        receipt = gk.verify_state_transition(
            x_current=0.4, r_parameter=3.1,
            steward_attestation=valid_attestation, payload_data=payload
        )
        assert receipt["trajectory_metrics"]["resulting_state"] == pytest.approx(
            7 / 12, abs=1e-6
        )

    def test_chaotic_r_marks_torque_stall(self, gk, valid_attestation, payload):
        receipt = gk.verify_state_transition(
            x_current=0.4, r_parameter=3.1,
            steward_attestation=valid_attestation, payload_data=payload
        )
        assert receipt["error_telemetry"]["torque_stall_triggered"] is True

    def test_chaotic_r_marks_breach(self, gk, valid_attestation, payload):
        receipt = gk.verify_state_transition(
            x_current=0.4, r_parameter=3.1,
            steward_attestation=valid_attestation, payload_data=payload
        )
        assert receipt["error_telemetry"]["admissibility_breach"] is True

    def test_chaotic_r_zeroes_nullifier(self, gk, valid_attestation, payload):
        receipt = gk.verify_state_transition(
            x_current=0.4, r_parameter=3.1,
            steward_attestation=valid_attestation, payload_data=payload
        )
        assert receipt["steward_signature_nullifier"] == "0x" + "0" * 40

    def test_chaotic_r_receipt_code_contains_trajectory_breach(self, gk, valid_attestation, payload):
        receipt = gk.verify_state_transition(
            x_current=0.4, r_parameter=3.1,
            steward_attestation=valid_attestation, payload_data=payload
        )
        assert "Trajectory_Breach" in receipt["error_telemetry"]["receipt_code"]

    def test_extreme_r_is_halted(self, gk, valid_attestation, payload):
        receipt = gk.verify_state_transition(
            x_current=0.5, r_parameter=100.0,
            steward_attestation=valid_attestation, payload_data=payload
        )
        assert receipt["execution_status"].startswith("HALTED_AND_VISIBLE")

    def test_zero_r_is_admissible(self, gk, valid_attestation, payload):
        receipt = gk.verify_state_transition(
            x_current=0.5, r_parameter=0.0,
            steward_attestation=valid_attestation, payload_data=payload
        )
        assert receipt["execution_status"] == "ADMISSIBLE_AND_SEALED"
        assert receipt["trajectory_metrics"]["resulting_state"] == pytest.approx(0.0)

    def test_negative_r_is_admissible(self, gk, valid_attestation, payload):
        """Negative r values are below the chaos threshold and pass the geometric gate."""
        receipt = gk.verify_state_transition(
            x_current=0.5, r_parameter=-1.0,
            steward_attestation=valid_attestation, payload_data=payload
        )
        assert receipt["execution_status"] == "ADMISSIBLE_AND_SEALED"


# ---------------------------------------------------------------------------
# Admissible state evolution
# ---------------------------------------------------------------------------

class TestAdmissibleStateEvolution:
    """When both gates pass, the logistic map advances correctly."""

    def test_admissible_status(self, gk, valid_attestation, payload):
        receipt = gk.verify_state_transition(
            x_current=0.4, r_parameter=2.2,
            steward_attestation=valid_attestation, payload_data=payload
        )
        assert receipt["execution_status"] == "ADMISSIBLE_AND_SEALED"

    def test_admissible_logistic_map_calculation(self, gk, valid_attestation, payload):
        x, r = 0.4, 2.2
        expected = round(r * x * (1 - x), 6)
        receipt = gk.verify_state_transition(
            x_current=x, r_parameter=r,
            steward_attestation=valid_attestation, payload_data=payload
        )
        assert receipt["trajectory_metrics"]["resulting_state"] == pytest.approx(expected)

    def test_admissible_r_parameter_echoed(self, gk, valid_attestation, payload):
        receipt = gk.verify_state_transition(
            x_current=0.4, r_parameter=1.8,
            steward_attestation=valid_attestation, payload_data=payload
        )
        assert receipt["trajectory_metrics"]["r_parameter"] == pytest.approx(1.8)

    def test_admissible_nullifier_echoed(self, gk, valid_attestation, payload):
        receipt = gk.verify_state_transition(
            x_current=0.4, r_parameter=2.0,
            steward_attestation=valid_attestation, payload_data=payload
        )
        assert receipt["steward_signature_nullifier"] == valid_attestation["nullifier"]

    def test_admissible_no_breach(self, gk, valid_attestation, payload):
        receipt = gk.verify_state_transition(
            x_current=0.4, r_parameter=2.0,
            steward_attestation=valid_attestation, payload_data=payload
        )
        assert receipt["error_telemetry"]["admissibility_breach"] is False
        assert receipt["error_telemetry"]["torque_stall_triggered"] is False

    def test_admissible_receipt_code_is_none(self, gk, valid_attestation, payload):
        receipt = gk.verify_state_transition(
            x_current=0.4, r_parameter=2.0,
            steward_attestation=valid_attestation, payload_data=payload
        )
        assert receipt["error_telemetry"]["receipt_code"] == "LogosRefusalReceipt::None"

    def test_admissible_x_near_zero(self, gk, valid_attestation, payload):
        x, r = 0.01, 2.0
        expected = round(r * x * (1 - x), 6)
        receipt = gk.verify_state_transition(
            x_current=x, r_parameter=r,
            steward_attestation=valid_attestation, payload_data=payload
        )
        assert receipt["trajectory_metrics"]["resulting_state"] == pytest.approx(expected)

    def test_admissible_x_near_one(self, gk, valid_attestation, payload):
        x, r = 0.99, 1.5
        expected = round(r * x * (1 - x), 6)
        receipt = gk.verify_state_transition(
            x_current=x, r_parameter=r,
            steward_attestation=valid_attestation, payload_data=payload
        )
        assert receipt["trajectory_metrics"]["resulting_state"] == pytest.approx(expected)


# ---------------------------------------------------------------------------
# Receipt structure and state commitment determinism
# ---------------------------------------------------------------------------

class TestReceiptStructure:
    """Every receipt carries a SHA-256 payload commitment regardless of outcome."""

    def _expected_root(self, payload: dict) -> str:
        b = json.dumps(payload, sort_keys=True).encode("utf-8")
        return "0x" + hashlib.sha256(b).hexdigest()

    def test_admissible_commitment_root_correct(self, gk, valid_attestation, payload):
        receipt = gk.verify_state_transition(
            x_current=0.4, r_parameter=2.0,
            steward_attestation=valid_attestation, payload_data=payload
        )
        assert receipt["state_commitment_root"] == self._expected_root(payload)

    def test_tier0_refusal_commitment_root_correct(self, gk, payload):
        receipt = gk.verify_state_transition(
            x_current=0.4, r_parameter=2.0,
            steward_attestation=None, payload_data=payload
        )
        assert receipt["state_commitment_root"] == self._expected_root(payload)

    def test_chaotic_refusal_commitment_root_correct(self, gk, valid_attestation, payload):
        receipt = gk.verify_state_transition(
            x_current=0.4, r_parameter=3.1,
            steward_attestation=valid_attestation, payload_data=payload
        )
        assert receipt["state_commitment_root"] == self._expected_root(payload)

    def test_commitment_is_deterministic(self, gk, valid_attestation, payload):
        r1 = gk.verify_state_transition(0.4, 2.0, valid_attestation, payload)
        r2 = gk.verify_state_transition(0.4, 2.0, valid_attestation, payload)
        assert r1["state_commitment_root"] == r2["state_commitment_root"]

    def test_different_payloads_produce_different_roots(self, gk, valid_attestation):
        p1 = {"action": "alpha"}
        p2 = {"action": "beta"}
        r1 = gk.verify_state_transition(0.4, 2.0, valid_attestation, p1)
        r2 = gk.verify_state_transition(0.4, 2.0, valid_attestation, p2)
        assert r1["state_commitment_root"] != r2["state_commitment_root"]

    def test_receipt_has_all_required_keys_admissible(self, gk, valid_attestation, payload):
        receipt = gk.verify_state_transition(0.4, 2.0, valid_attestation, payload)
        for key in ("execution_status", "state_commitment_root",
                    "steward_signature_nullifier", "trajectory_metrics", "error_telemetry"):
            assert key in receipt, f"Missing key: {key}"

    def test_receipt_has_all_required_keys_refused(self, gk, payload):
        receipt = gk.verify_state_transition(0.4, 2.0, None, payload)
        for key in ("execution_status", "state_commitment_root",
                    "steward_signature_nullifier", "trajectory_metrics", "error_telemetry"):
            assert key in receipt, f"Missing key: {key}"

    def test_commitment_root_has_0x_prefix(self, gk, valid_attestation, payload):
        receipt = gk.verify_state_transition(0.4, 2.0, valid_attestation, payload)
        assert receipt["state_commitment_root"].startswith("0x")

    def test_commitment_root_is_64_hex_chars_after_prefix(self, gk, valid_attestation, payload):
        receipt = gk.verify_state_transition(0.4, 2.0, valid_attestation, payload)
        root_hex = receipt["state_commitment_root"][2:]
        assert len(root_hex) == 64
        assert all(c in "0123456789abcdef" for c in root_hex)


# ---------------------------------------------------------------------------
# Configuration — custom limits
# ---------------------------------------------------------------------------

class TestCustomConfiguration:
    """DigitalRepublicGatekeeper respects non-default contraction limits."""

    def test_custom_lower_limit_blocks_r_below_default(self, valid_attestation, payload):
        gk = DigitalRepublicGatekeeper(global_contraction_limit=1.5)
        receipt = gk.verify_state_transition(
            x_current=0.4, r_parameter=1.6,
            steward_attestation=valid_attestation, payload_data=payload
        )
        assert "TORQUE_STALL_TRIGGERED" in receipt["execution_status"]

    def test_custom_lower_limit_admits_r_at_boundary(self, valid_attestation, payload):
        gk = DigitalRepublicGatekeeper(global_contraction_limit=1.5)
        receipt = gk.verify_state_transition(
            x_current=0.4, r_parameter=1.5,
            steward_attestation=valid_attestation, payload_data=payload
        )
        assert receipt["execution_status"] == "ADMISSIBLE_AND_SEALED"

    def test_custom_inert_constant_used_on_refusal(self, valid_attestation, payload):
        gk = DigitalRepublicGatekeeper(inert_constant=0.5)
        receipt = gk.verify_state_transition(
            x_current=0.4, r_parameter=3.0,
            steward_attestation=valid_attestation, payload_data=payload
        )
        assert receipt["trajectory_metrics"]["resulting_state"] == pytest.approx(0.5)

    def test_default_limit_is_2_4(self):
        gk = DigitalRepublicGatekeeper()
        assert gk.r_limit == pytest.approx(2.4)

    def test_default_inert_constant_is_7_over_12(self):
        gk = DigitalRepublicGatekeeper()
        assert gk.inert_target == pytest.approx(7 / 12, abs=1e-9)


# ---------------------------------------------------------------------------
# PR canonical script — regression cases
# ---------------------------------------------------------------------------

class TestPRCanonicalCases:
    """Exact test cases from the PR's __main__ block must produce correct receipts."""

    def test_case1_admissible_r_2_2(self, gk, valid_attestation):
        payload = {"module": "Registry_State_Transition", "action": "Commit_State"}
        receipt = gk.verify_state_transition(
            x_current=0.4, r_parameter=2.2,
            steward_attestation=valid_attestation, payload_data=payload
        )
        assert receipt["execution_status"] == "ADMISSIBLE_AND_SEALED"
        # x_{n+1} = 2.2 * 0.4 * 0.6 = 0.528
        assert receipt["trajectory_metrics"]["resulting_state"] == pytest.approx(0.528, abs=1e-5)

    def test_case2_chaotic_r_3_1(self, gk, valid_attestation):
        payload = {"module": "Registry_State_Transition", "action": "Commit_State"}
        receipt = gk.verify_state_transition(
            x_current=0.4, r_parameter=3.1,
            steward_attestation=valid_attestation, payload_data=payload
        )
        assert receipt["execution_status"].startswith("HALTED_AND_VISIBLE")
        assert receipt["trajectory_metrics"]["resulting_state"] == pytest.approx(7 / 12, abs=1e-6)
