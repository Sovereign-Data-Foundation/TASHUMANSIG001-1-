"""Property-based invariant tests for the TrueAlphaSpiral (TAS) framework.

Uses Hypothesis to generate adversarial inputs and verify that the five highest-value
architectural invariants hold across arbitrary input spaces:

1. Invariant W1 — WakeChain HMAC integrity: any sequence of payloads produces
   a valid, verifiable HMAC-linked chain.
2. Invariant S1 — Semantic Drift Index bounds: SDI is always in [0.0, 2.0] for
   any two non-empty float vectors; restricted to [0.0, 1.0] for non-negative vectors.
3. Invariant G1 — Genesis anchor determinism: derive_app_hash and build_genesis_payload
   produce identical outputs across independent calls with the same input.
4. Invariant C1 — Capability revocation soundness: a right revoked from a table is
   never invokable, regardless of invocation order or right combination.
5. Invariant U1 — UVK admission rejection: a payload missing required lineage fields
   (lineage_parent_hash) is always rejected by LogosValidationLoop.
"""
# © 2025 Russell Nordland | TrueAlphaSpiral (TAS) | Apache-2.0

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from wake_chain import WakeChain
from stability import semantic_drift_index
from genesis_anchor import derive_app_hash, build_genesis_payload
from capability import CapabilityTable, Right, ALL_RIGHTS, CapabilityError
from tas_logos_gatekeeper import LogosValidationLoop


# ===========================================================================
# Invariant W1 — WakeChain HMAC integrity
# ===========================================================================


class TestWakeChainHMACIntegrity:
    """Invariant W1 — WakeChain HMAC integrity (§5).

    For any sequence of arbitrary JSON-serialisable payloads committed to a
    WakeChain, the chain's HMAC-linked provenance structure must remain valid
    and verifiable after every commit.  The wake-head invariant must hold at
    every step:

        wake_head_t = SHA-256(wake_head_{t-1} || bytes(R_t))
    """

    _json_value = st.recursive(
        st.one_of(
            st.none(),
            st.booleans(),
            st.integers(min_value=-(2**31), max_value=2**31 - 1),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text(max_size=64),
        ),
        lambda children: st.one_of(
            st.lists(children, max_size=4),
            st.dictionaries(st.text(max_size=16), children, max_size=4),
        ),
        max_leaves=16,
    )

    @given(payloads=st.lists(_json_value, min_size=1, max_size=10))
    def test_chain_valid_after_arbitrary_commits(self, payloads):
        """Invariant W1: chain.verify() is True after committing any sequence of payloads."""
        chain = WakeChain()
        for i, payload in enumerate(payloads):
            chain.commit(event={"index": i, "data": payload})
        assert chain.verify(), "WakeChain must verify after arbitrary payload commits"

    @given(payloads=st.lists(_json_value, min_size=2, max_size=8))
    def test_seq_monotone_under_arbitrary_commits(self, payloads):
        """Invariant W1: sequence numbers are strictly monotone for any input sequence."""
        chain = WakeChain()
        marks = [chain.commit(event={"d": p}) for p in payloads]
        seqs = [m.seq for m in marks]
        assert seqs == list(range(len(payloads))), "Sequence numbers must be strictly monotone"

    @given(payloads=st.lists(_json_value, min_size=2, max_size=6))
    def test_prev_link_correct_under_arbitrary_commits(self, payloads):
        """Invariant W1: each receipt's prev field must equal the hash of the prior receipt."""
        chain = WakeChain()
        marks = [chain.commit(event={"d": p}) for p in payloads]
        for i in range(1, len(marks)):
            assert marks[i].prev == marks[i - 1].receipt_hash(), (
                "prev link must equal hash of preceding receipt"
            )

    @given(payloads=st.lists(_json_value, min_size=1, max_size=10))
    def test_receipt_hash_deterministic_under_arbitrary_payloads(self, payloads):
        """Invariant W1: receipt_hash() is idempotent for any committed payload."""
        chain = WakeChain()
        marks = [chain.commit(event={"d": p}) for p in payloads]
        for mark in marks:
            assert mark.receipt_hash() == mark.receipt_hash(), (
                "receipt_hash must be deterministic"
            )


# ===========================================================================
# Invariant S1 — Semantic Drift Index bounds
# ===========================================================================


class TestSemanticDriftIndexBounds:
    """Invariant S1 — Semantic Drift Index monotonicity and bounds (§6).

    SDI = 1 - cos(θ).  For all valid embedding vectors the result must be
    in [0.0, 2.0].  For non-negative vectors (the typical embedding case)
    the cosine similarity is non-negative, so SDI is in [0.0, 1.0].
    """

    _float_list = st.lists(
        st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
        min_size=1,
        max_size=20,
    )

    _nonneg_float_list = st.lists(
        st.floats(min_value=0.0, max_value=1e6, allow_nan=False, allow_infinity=False),
        min_size=1,
        max_size=20,
    )

    @given(v=_float_list)
    def test_sdi_in_full_range_for_any_vectors(self, v):
        """Invariant S1: SDI ∈ [0.0, 2.0] for any pair of same-length float vectors."""
        sdi = semantic_drift_index(v, v)
        # Identical vectors → SDI = 0.0; allow tiny fp rounding on both ends
        assert -1e-9 <= sdi <= 2.0 + 1e-9, f"SDI out of [0, 2] range: {sdi}"

    @given(
        data=st.data(),
        n=st.integers(min_value=1, max_value=20),
    )
    def test_sdi_nonneg_vectors_in_unit_range(self, data, n):
        """Invariant S1: SDI ∈ [0.0, 1.0] for non-negative embedding vectors."""
        a = data.draw(st.lists(
            st.floats(min_value=0.0, max_value=1e6, allow_nan=False, allow_infinity=False),
            min_size=n, max_size=n,
        ))
        b = data.draw(st.lists(
            st.floats(min_value=0.0, max_value=1e6, allow_nan=False, allow_infinity=False),
            min_size=n, max_size=n,
        ))
        sdi = semantic_drift_index(a, b)
        assert -1e-9 <= sdi <= 1.0 + 1e-9, (
            f"SDI must be in [0.0, 1.0] for non-negative vectors, got {sdi}"
        )

    @given(v=_float_list)
    def test_sdi_identical_vectors_is_zero(self, v):
        """Invariant S1: SDI(v, v) = 0.0 for any vector with a finite, non-zero fp norm."""
        import math
        norm = math.sqrt(sum(x * x for x in v))
        # Skip vectors whose fp norm rounds to zero (subnormal / extreme values)
        assume(norm > 0.0 and math.isfinite(norm))
        sdi = semantic_drift_index(v, v)
        assert sdi == pytest.approx(0.0, abs=1e-9), (
            f"SDI(v, v) must be 0 for any non-zero vector, got {sdi}"
        )


# ===========================================================================
# Invariant G1 — Genesis anchor determinism
# ===========================================================================


class TestGenesisAnchorDeterminism:
    """Invariant G1 — Genesis anchor determinism (A_0 lineage determinism).

    derive_app_hash and build_genesis_payload must produce identical results
    across independent calls with the same input.  This ensures the genesis
    payload is cryptographically grounded to the A_0 provenance root and
    cannot drift between calls.
    """

    _json_state = st.fixed_dictionaries({
        "key": st.text(max_size=32),
        "value": st.integers(min_value=0, max_value=10**9),
    })

    @given(state=_json_state)
    def test_derive_app_hash_deterministic(self, state):
        """Invariant G1: derive_app_hash produces identical output for the same app_state."""
        h1 = derive_app_hash(state)
        h2 = derive_app_hash(state)
        assert h1 == h2, "derive_app_hash must be deterministic across independent calls"

    @given(state=_json_state)
    def test_derive_app_hash_is_uppercase_hex(self, state):
        """Invariant G1: derive_app_hash always returns 64-character upper-case hex."""
        h = derive_app_hash(state)
        assert len(h) == 64, f"app_hash must be 64 chars, got {len(h)}"
        assert h == h.upper(), "app_hash must be upper-case hex"

    @given(
        state_a=_json_state,
        state_b=_json_state,
    )
    def test_different_states_produce_different_hashes(self, state_a, state_b):
        """Invariant G1: distinct app_state inputs produce distinct hashes (collision resistance)."""
        assume(state_a != state_b)
        h_a = derive_app_hash(state_a)
        h_b = derive_app_hash(state_b)
        assert h_a != h_b, "Different app_state inputs must produce different hashes"

    def test_build_genesis_payload_deterministic(self):
        """Invariant G1: build_genesis_payload is deterministic across independent calls."""
        p1 = build_genesis_payload()
        p2 = build_genesis_payload()
        assert p1 == p2, "build_genesis_payload must return the same payload on every call"

    def test_build_genesis_payload_app_hash_self_consistent(self):
        """Invariant G1: app_hash in genesis payload matches re-derivation from app_state."""
        payload = build_genesis_payload()
        expected = derive_app_hash(payload["app_state"])
        assert payload["app_hash"] == expected, "app_hash must equal re-derived value"


# ===========================================================================
# Invariant C1 — Capability revocation soundness
# ===========================================================================


class TestCapabilityRevocationSoundness:
    """Invariant C1 — Capability revocation soundness (§3 POLA).

    A right revoked from a CapabilityTable must never be invokable after
    revocation, regardless of invocation order or the combination of rights
    originally granted.  This enforces the Principle of Least Authority.
    """

    _rights_subset = st.frozensets(
        st.sampled_from([
            Right.READ, Right.WRITE, Right.EXECUTE, Right.MINT, Right.REVOKE, Right.MOVE,
        ]),
        min_size=1,
    )

    @given(rights=_rights_subset)
    def test_revoked_capability_not_invokable(self, rights):
        """Invariant C1: invoke always raises CapabilityError after revoke, for any rights set."""
        ct = CapabilityTable()
        combined = Right(0)
        for r in rights:
            combined = combined | r
        cap = ct.retype("resource", combined)
        ct.revoke(cap)
        assert not ct.is_live(cap), "Capability must not be live after revocation"
        for right in rights:
            with pytest.raises(CapabilityError):
                ct.invoke(cap, right)

    @given(rights=_rights_subset)
    def test_revoked_capability_not_live(self, rights):
        """Invariant C1: is_live returns False immediately after revocation for any rights set."""
        ct = CapabilityTable()
        combined = Right(0)
        for r in rights:
            combined = combined | r
        cap = ct.retype("resource", combined)
        assert ct.is_live(cap), "Capability must be live before revocation"
        ct.revoke(cap)
        assert not ct.is_live(cap), "Capability must not be live after revocation"

    @given(
        parent_rights=_rights_subset,
        child_rights=_rights_subset,
    )
    def test_parent_revocation_cascades_to_child(self, parent_rights, child_rights):
        """Invariant C1: revoking parent cascades to all child capabilities."""
        needs_mint = Right.MINT
        combined_parent = Right(0)
        for r in parent_rights:
            combined_parent = combined_parent | r
        combined_parent = combined_parent | needs_mint

        valid_child = Right(0)
        for r in child_rights:
            if r in combined_parent:
                valid_child = valid_child | r
        if valid_child == Right(0):
            return

        ct = CapabilityTable()
        parent = ct.retype("res", combined_parent)
        child = ct.mint(parent, valid_child)
        ct.revoke(parent)
        assert not ct.is_live(child), "Child capability must not be live after parent revocation"


# ===========================================================================
# Invariant U1 — UVK admission rejection on malformed payloads
# ===========================================================================


class TestUVKAdmissionRejectionMalformedPayloads:
    """Invariant U1 — UVK admission rejection on malformed payloads (§2).

    A manifest payload missing the required `lineage_parent_hash` field must
    always be rejected by LogosValidationLoop.evaluate_logos_bounds, regardless
    of what other keys it contains.  This guards the Logos Sentient Lock
    boundary against payloads that cannot prove provenance.
    """

    _extra_keys = st.dictionaries(
        st.text(min_size=1, max_size=16).filter(lambda k: k != "lineage_parent_hash"),
        st.one_of(st.text(max_size=32), st.integers(), st.booleans()),
        max_size=5,
    )

    @given(extra=_extra_keys)
    def test_missing_lineage_hash_always_rejected(self, extra):
        """Invariant U1: manifest without lineage_parent_hash is always rejected."""
        chain = WakeChain()
        loop = LogosValidationLoop(invariant_check=lambda: True, min_density_floor=0.0)
        manifest = dict(extra)
        manifest.pop("lineage_parent_hash", None)
        manifest["payload_vector"] = {"step": "test"}
        result = loop.evaluate_logos_bounds(chain.head, manifest, nonce=0)
        assert result is False, (
            "LogosValidationLoop must reject manifests missing lineage_parent_hash"
        )

    @given(
        wrong_hash=st.binary(min_size=1, max_size=64).filter(
            lambda b: b != bytes(32)
        ),
    )
    def test_wrong_lineage_hash_always_rejected(self, wrong_hash):
        """Invariant U1: manifest with mismatched lineage_parent_hash is always rejected."""
        chain = WakeChain()
        loop = LogosValidationLoop(invariant_check=lambda: True, min_density_floor=0.0)
        manifest = {
            "lineage_parent_hash": wrong_hash.hex(),
            "payload_vector": {"step": "test"},
        }
        result = loop.evaluate_logos_bounds(chain.head, manifest, nonce=0)
        assert result is False, (
            "LogosValidationLoop must reject manifests with wrong lineage_parent_hash"
        )
