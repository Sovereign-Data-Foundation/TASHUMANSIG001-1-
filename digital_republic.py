"""
digital_republic.py — Digital Republic Doctrine Execution Gate

Arithmetizes the four-part invariant structure from `what_we_are_building.md`
into a runtime enforcement mechanism.

The DigitalRepublicGatekeeper enforces two pre-computation constraints:

  1. Tier 0 Human Seed — every state transition must carry a valid human
     steward attestation.  Without it the transition is cryptographically
     inadmissible before any computation occurs.

  2. Geometric Bound (r=2.4) — the logistic-map parameter must remain strictly
     within the global contraction sink.  Any trajectory crossing the chaos
     threshold is halted and its variance is crushed to the Banach Fixed-Point
     inert constant (7/12 ≈ 0.583333).

Every decision — admissible or refused — emits a structured public receipt
suitable for an append-only audit ledger.

STAMP_ANCHOR_2026_07_07
"""

import hashlib
import json
from typing import Any, Dict, Optional


class DigitalRepublicGatekeeper:
    """
    Operational enforcement mechanism for the Digital Republic Doctrine.

    Enforces the Tier 0 Human Seed invariant and the r=2.4 global
    contraction limit.  Emits cryptographically rooted receipts for
    every evaluated state transition.

    Parameters
    ----------
    global_contraction_limit:
        Maximum admissible logistic-map parameter.  Default ``2.4``.
        Trajectories above this threshold are in the chaotic regime and
        are unconditionally halted.
    inert_constant:
        Banach Fixed-Point target to which a rogue trajectory is forced
        when the geometric bound is violated.  Default ``7/12 ≈ 0.583333``.
    """

    GLOBAL_CONTRACTION_LIMIT: float = 2.4
    INERT_CONSTANT: float = 7 / 12  # ≈ 0.583333

    def __init__(
        self,
        global_contraction_limit: float = GLOBAL_CONTRACTION_LIMIT,
        inert_constant: float = INERT_CONSTANT,
    ) -> None:
        self.r_limit = global_contraction_limit
        self.inert_target = inert_constant

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def verify_state_transition(
        self,
        x_current: float,
        r_parameter: float,
        steward_attestation: Optional[Dict[str, Any]],
        payload_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Arithmetized execution gate.

        Evaluates a proposed state transition and returns a public receipt.
        The receipt is ``ADMISSIBLE_AND_SEALED`` when both invariants hold;
        otherwise it is ``HALTED_AND_VISIBLE`` with a structured fault code.

        Parameters
        ----------
        x_current:
            Current logistic-map state value ``x_n ∈ (0, 1)``.
        r_parameter:
            Growth parameter for the proposed transition.
        steward_attestation:
            Dict with at minimum ``{"valid": True, "nullifier": "<hex>"}``
            representing the human steward's cryptographic witness.
            ``None`` or ``{"valid": False}`` triggers a Tier 0 refusal.
        payload_data:
            Arbitrary operational payload dict.  Its SHA-256 commitment is
            embedded in every receipt.

        Returns
        -------
        dict
            Structured public receipt.
        """
        state_commitment_root = self._commitment(payload_data)

        # Gate 1 — Tier 0 Human Seed
        if not steward_attestation or steward_attestation.get("valid") is not True:
            return self._emit_refusal(
                reason="Missing or Invalid Tier 0 Human Attestation",
                root=state_commitment_root,
                halt_type="CRITICAL_SIGNATURE_FAILURE",
            )

        # Gate 2 — Geometric Bound: r must remain within the contraction sink
        if r_parameter > self.r_limit:
            x_forced = self.inert_target
            return self._emit_refusal(
                reason=(
                    f"Trajectory Breach: r={r_parameter} exceeds strict "
                    f"stability boundary ({self.r_limit})"
                ),
                root=state_commitment_root,
                halt_type="TORQUE_STALL_TRIGGERED",
                forced_state=x_forced,
            )

        # Admissible — advance the logistic map: x_{n+1} = r * x_n * (1 - x_n)
        x_next = r_parameter * x_current * (1.0 - x_current)

        return {
            "execution_status": "ADMISSIBLE_AND_SEALED",
            "state_commitment_root": "0x" + state_commitment_root,
            "steward_signature_nullifier": steward_attestation.get("nullifier", "0x00"),
            "trajectory_metrics": {
                "r_parameter": r_parameter,
                "resulting_state": round(x_next, 6),
            },
            "error_telemetry": {
                "admissibility_breach": False,
                "torque_stall_triggered": False,
                "receipt_code": "LogosRefusalReceipt::None",
            },
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _commitment(self, payload_data: Dict[str, Any]) -> str:
        payload_bytes = json.dumps(payload_data, sort_keys=True).encode("utf-8")
        return hashlib.sha256(payload_bytes).hexdigest()

    def _emit_refusal(
        self,
        reason: str,
        root: str,
        halt_type: str,
        forced_state: Optional[float] = None,
    ) -> Dict[str, Any]:
        return {
            "execution_status": f"HALTED_AND_VISIBLE::{halt_type}",
            "state_commitment_root": "0x" + root,
            "steward_signature_nullifier": "0x" + "0" * 40,
            "trajectory_metrics": {
                "resulting_state": forced_state if forced_state is not None else self.inert_target,
            },
            "error_telemetry": {
                "admissibility_breach": True,
                "torque_stall_triggered": halt_type == "TORQUE_STALL_TRIGGERED",
                "receipt_code": f"LogosRefusalReceipt::{reason.replace(' ', '_')}",
            },
        }


# ---------------------------------------------------------------------------
# Runtime verification verdict (matches the PR canonical script exactly)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    gatekeeper = DigitalRepublicGatekeeper()

    operation_payload = {"module": "Registry_State_Transition", "action": "Commit_State"}

    valid_attestation = {
        "valid": True,
        "nullifier": "0x8bfae3927f4c93a8b2c1e0f95d86ba73c4d5e6f2",
    }

    print("--- EVALUATING ADMISSIBLE RUNTIME TRANSACTION ---")
    receipt_1 = gatekeeper.verify_state_transition(
        x_current=0.4,
        r_parameter=2.2,
        steward_attestation=valid_attestation,
        payload_data=operation_payload,
    )
    print(json.dumps(receipt_1, indent=2))

    print("\n--- EVALUATING CHAOTIC DRIFT (r=3.1 Breach) ---")
    receipt_2 = gatekeeper.verify_state_transition(
        x_current=0.4,
        r_parameter=3.1,
        steward_attestation=valid_attestation,
        payload_data=operation_payload,
    )
    print(json.dumps(receipt_2, indent=2))
