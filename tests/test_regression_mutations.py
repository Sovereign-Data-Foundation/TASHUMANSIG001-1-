"""Invariant regression mutation tests (Task 2).

These tests verify that the TAS enforcement code correctly *rejects* adversarial
inputs.  They act as "mutation sentinels": if a future refactor accidentally
removes a guard, these tests will catch it before production.

Each test class targets one architectural boundary and deliberately presents a
malformed or adversarial payload to prove the guard is present and active.

Coverage:
- W1/W3: WakeChain HMAC tamper detection & sequence replay
- C1/C2: Capability revocation and cascade soundness
- U1/U5: UVK authorization rejection and Logos lineage gate
- P0/P1: Axiom violation detection
- X4:    TruthAudit strain ceiling enforcement
- X5:    PSVP entropy floor and spec chaining integrity
- U6:    Sovereign accountability scope enforcement
"""
# © 2025 Russell Nordland | TrueAlphaSpiral (TAS) | Apache-2.0

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from wake_chain import WakeChain
from capability import CapabilityTable, CapabilityError, Right
from uvk import UVK, Invariant, AdmissionStatus
from tas_logos_gatekeeper import LogosValidationLoop
from axioms import P0Equivalence, P1Admissibility, AdmissibilityClause, AxiomViolation
from truth_audit import TruthAuditEngine, StrainCeilingBreached, DimensionScore, AuditDimension
from psvp import PSVP, DriftGateError
from sovereign_accountability import (
    SovereignAccountability, DualSovereignty, FactionSubordination,
    BranchScope, Branch, SovereigntyTier, SubordinationError,
)


# ===========================================================================
# W1/W3 — WakeChain tamper & replay regression sentinels
# ===========================================================================


class TestWakeChainTamperRegressions:
    """Regression sentinels for W1 HMAC tamper detection and W3 anti-replay.

    If the HMAC or sequence-number guards are removed, these tests fail.
    """

    def test_mutated_sig_fails_verify(self):
        """W1: flipping one byte in a receipt's HMAC sig breaks chain.verify()."""
        chain = WakeChain()
        chain.commit({"step": "a"})
        chain.commit({"step": "b"})
        pm = chain._receipts[0]
        bad_sig = bytes([pm.sig[0] ^ 0xFF]) + pm.sig[1:]
        chain._receipts[0] = pm.__class__(
            id=pm.id, seq=pm.seq, prev=pm.prev,
            key_commit=pm.key_commit, event_hash=pm.event_hash,
            info=pm.info, sig=bad_sig,
        )
        assert not chain.verify(), "Tampered HMAC must cause verify() to return False"

    def test_mutated_prev_fails_verify(self):
        """W1: corrupting the prev-link breaks chain.verify()."""
        chain = WakeChain()
        chain.commit({"step": "a"})
        chain.commit({"step": "b"})
        pm = chain._receipts[1]
        bad_prev = bytes([pm.prev[0] ^ 0x01]) + pm.prev[1:]
        chain._receipts[1] = pm.__class__(
            id=pm.id, seq=pm.seq, prev=bad_prev,
            key_commit=pm.key_commit, event_hash=pm.event_hash,
            info=pm.info, sig=pm.sig,
        )
        assert not chain.verify()

    def test_duplicate_seq_fails_verify(self):
        """W3: inserting a duplicate seq number breaks chain.verify()."""
        chain = WakeChain()
        chain.commit({"step": "a"})
        pm0 = chain._receipts[0]
        # Inject a receipt with seq=0 again
        chain._receipts.append(pm0)
        assert not chain.verify()

    def test_out_of_order_seq_fails_verify(self):
        """W3: swapping two receipts breaks sequence monotonicity."""
        chain = WakeChain()
        chain.commit({"step": "a"})
        chain.commit({"step": "b"})
        chain._receipts[0], chain._receipts[1] = chain._receipts[1], chain._receipts[0]
        assert not chain.verify()

    def test_wrong_key_fails_sig_verify(self):
        """W1: verifying with the wrong key returns False."""
        chain = WakeChain(uvk_key=b"correct-key" + bytes(21))
        pm = chain.commit({"step": "a"})
        assert not pm.verify_sig(b"wrong-key" + bytes(23))


# ===========================================================================
# C1/C2 — Capability revocation regression sentinels
# ===========================================================================


class TestCapabilityRevocationRegressions:
    """Regression sentinels for C1 (revocation soundness) and C2 (cascade).

    If the revocation check is bypassed, invoke() would succeed post-revoke.
    """

    def test_revoked_cap_cannot_execute(self):
        """C1: invoke with EXECUTE raises after revocation."""
        ct = CapabilityTable()
        cap = ct.retype("res", Right.EXECUTE)
        ct.revoke(cap)
        with pytest.raises(CapabilityError):
            ct.invoke(cap, Right.EXECUTE)

    def test_revoked_cap_cannot_read(self):
        """C1: invoke with READ raises after revocation, even if READ was granted."""
        ct = CapabilityTable()
        cap = ct.retype("res", Right.READ | Right.EXECUTE)
        ct.revoke(cap)
        with pytest.raises(CapabilityError):
            ct.invoke(cap, Right.READ)

    def test_cascade_revocation(self):
        """C2: revoking parent cascades to child — child invoke raises."""
        ct = CapabilityTable()
        parent = ct.retype("res", Right.EXECUTE | Right.MINT)
        child = ct.mint(parent, Right.EXECUTE)
        ct.revoke(parent)
        with pytest.raises(CapabilityError):
            ct.invoke(child, Right.EXECUTE)

    def test_child_cannot_exceed_parent_rights(self):
        """C3: minting a child with rights ⊄ parent raises CapabilityError."""
        ct = CapabilityTable()
        parent = ct.retype("res", Right.READ | Right.MINT)
        with pytest.raises(CapabilityError):
            ct.mint(parent, Right.EXECUTE)  # EXECUTE not in parent

    def test_foreign_cap_rejected(self):
        """C4: a capability not registered in the table is rejected."""
        ct1 = CapabilityTable()
        ct2 = CapabilityTable()
        cap = ct1.retype("res", Right.EXECUTE)
        with pytest.raises(CapabilityError):
            ct2.invoke(cap, Right.EXECUTE)


# ===========================================================================
# U1/U5 — UVK authorization & Logos gate regression sentinels
# ===========================================================================


class TestUVKRegressions:
    """Regression sentinels for U1 (admission control) and U5 (Logos gate)."""

    def test_cap_without_execute_or_mint_denied(self):
        """U1: capability lacking EXECUTE and MINT is denied at the perimeter."""
        uvk = UVK(wake_chain=WakeChain())
        cap = uvk.cap_table.retype("res", Right.READ)
        result = uvk.admit(cap, Right.READ, action="read-op")
        assert result.status == AdmissionStatus.DENIED_AUTHORIZATION

    def test_failing_invariant_denies_admission(self):
        """U1: a failing invariant prevents admission."""
        uvk = UVK(wake_chain=WakeChain())
        uvk.add_invariant(Invariant("always-false", "1.0", lambda x, a, u: False))
        cap = uvk.cap_table.retype("res", Right.EXECUTE)
        result = uvk.admit(cap, Right.EXECUTE, action="op")
        assert result.status == AdmissionStatus.DENIED_INVARIANT
        assert "always-false" in result.failed_invariants

    def test_logos_rejects_wrong_lineage(self):
        """U5: Logos gate rejects a manifest whose lineage hash doesn't match chain head."""
        chain = WakeChain()
        chain.commit({"step": "a"})
        loop = LogosValidationLoop(invariant_check=lambda: True, min_density_floor=0.0)
        manifest = {
            "lineage_parent_hash": "00" * 32,  # wrong — genesis, not current head
            "payload_vector": {"step": "test"},
        }
        assert not loop.evaluate_logos_bounds(chain.head, manifest, nonce=0)

    def test_logos_rejects_missing_lineage(self):
        """U5: Logos gate rejects a manifest with no lineage_parent_hash key."""
        chain = WakeChain()
        loop = LogosValidationLoop(invariant_check=lambda: True, min_density_floor=0.0)
        manifest = {"payload_vector": {"step": "test"}}
        assert not loop.evaluate_logos_bounds(chain.head, manifest, nonce=0)

    def test_revoked_cap_denied_by_uvk(self):
        """U1: a revoked capability is denied even if invariants pass."""
        uvk = UVK(wake_chain=WakeChain())
        cap = uvk.cap_table.retype("res", Right.EXECUTE)
        uvk.cap_table.revoke(cap)
        result = uvk.admit(cap, Right.EXECUTE, action="op")
        assert result.status == AdmissionStatus.DENIED_CAPABILITY


# ===========================================================================
# P0/P1 — Axiom violation regression sentinels
# ===========================================================================


class TestAxiomRegressions:
    """Regression sentinels for P0 (equivalence) and P1 (admissibility)."""

    def test_p0_rebind_raises(self):
        """P0: rebinding an already-bound symbol raises AxiomViolation."""
        p0 = P0Equivalence()
        p0.bind("alpha", "value-A")
        with pytest.raises(AxiomViolation):
            p0.bind("alpha", "value-B")

    def test_p0_validate_wrong_referent_raises(self):
        """P0: validating with a wrong referent raises AxiomViolation."""
        p0 = P0Equivalence()
        p0.bind("sym", "correct")
        with pytest.raises(AxiomViolation):
            p0.validate("sym", "wrong")

    def test_p1_failing_clause_raises(self):
        """P1: a failing admissibility clause raises AxiomViolation."""
        p1 = P1Admissibility()
        p1.add_clause(AdmissibilityClause("never", lambda t, p: False))
        with pytest.raises(AxiomViolation):
            p1.admit({"action": "op"})

    def test_p1_counter_increments_on_rejection(self):
        """P1: rejected_count increments for each failed admission."""
        p1 = P1Admissibility()
        p1.add_clause(AdmissibilityClause("never", lambda t, p: False))
        for _ in range(3):
            with pytest.raises(AxiomViolation):
                p1.admit({"action": "op"})
        assert p1.rejected_count == 3


# ===========================================================================
# X4 — TruthAudit strain ceiling regression sentinels
# ===========================================================================


class TestTruthAuditRegressions:
    """Regression sentinels for X4 strain ceiling enforcement."""

    def _scores(self, value: float):
        return [DimensionScore(dim, value) for dim in AuditDimension]

    def test_all_zero_scores_raises_strain_ceiling(self):
        """X4: all-zero scores exceed any positive strain ceiling."""
        engine = TruthAuditEngine(strain_ceiling=0.5)
        with pytest.raises(StrainCeilingBreached):
            engine.evaluate("test-action", scores=self._scores(0.0))

    def test_perfect_scores_do_not_raise(self):
        """X4: all-perfect scores produce zero strain, no exception."""
        engine = TruthAuditEngine(strain_ceiling=0.5)
        result = engine.evaluate("test-action", scores=self._scores(1.0))
        assert result.strain == pytest.approx(0.0, abs=1e-9)

    def test_strain_ceiling_boundary(self):
        """X4: strain = 1 - 0.5 = 0.5 exactly at ceiling is accepted."""
        engine = TruthAuditEngine(strain_ceiling=0.5)
        result = engine.evaluate("boundary", scores=self._scores(0.5))
        assert result.strain == pytest.approx(0.5, abs=1e-6)


# ===========================================================================
# X5 — PSVP entropy floor regression sentinels
# ===========================================================================


class TestPSVPRegressions:
    """Regression sentinels for X5 entropy floor and spec chaining."""

    def test_low_entropy_claim_rejected(self):
        """X5: a claim with entropy below the floor is rejected."""
        psvp = PSVP(min_density=10.0)  # impossibly high floor → rejection
        graph = psvp.decompose("a")    # single char → near-zero entropy
        with pytest.raises(DriftGateError):
            psvp.create_spec(graph)

    def test_spec_chain_predecessor_recorded(self):
        """X5: successor SpecArtifact records its predecessor's spec_id."""
        psvp = PSVP(min_density=0.0)
        art1 = psvp.create_spec(psvp.decompose("first proposal with enough distinct tokens"))
        art2 = psvp.create_spec(psvp.decompose("second proposal continues the chain further"))
        assert art2.predecessor_id == art1.spec_id

    def test_spec_id_changes_with_content(self):
        """X5: different content produces different spec_ids (tamper evidence)."""
        psvp = PSVP(min_density=0.0)
        art1 = psvp.create_spec(psvp.decompose("proposal alpha version one content here"))
        art2 = psvp.create_spec(psvp.decompose("proposal beta version two different text"))
        assert art1.spec_id != art2.spec_id


# ===========================================================================
# U6 — Sovereign accountability regression sentinels
# ===========================================================================


class TestSovereignAccountabilityRegressions:
    """Regression sentinels for U6 sovereignty scope enforcement."""

    def test_unregistered_entity_denied(self):
        """U6: an unregistered entity raises SubordinationError (audit check)."""
        sa = SovereignAccountability()
        # No entities registered — audit() raises SubordinationError
        with pytest.raises(SubordinationError):
            sa.authorised("unknown-entity", Branch.EXECUTIVE, SovereigntyTier.STATE, "act")

    def test_registered_entity_wrong_branch_denied(self):
        """U6: a registered entity is denied when the branch has no registered scope."""
        fs = FactionSubordination()
        fs.register_entity("agent-X")
        ds = DualSovereignty()
        # Register JUDICIAL/STATE but not EXECUTIVE/STATE
        ds.register(BranchScope(Branch.JUDICIAL, SovereigntyTier.STATE, ["read"]))
        sa = SovereignAccountability(dual_sovereignty=ds, faction_subordination=fs)
        result = sa.authorised("agent-X", Branch.EXECUTIVE, SovereigntyTier.STATE, "act")
        assert not result

    def test_registered_entity_correct_scope_admitted(self):
        """U6: a registered entity with the correct branch/tier/action is admitted."""
        fs = FactionSubordination()
        fs.register_entity("agent-Y")
        ds = DualSovereignty()
        ds.register(BranchScope(Branch.LEGISLATIVE, SovereigntyTier.STATE, ["vote"]))
        sa = SovereignAccountability(dual_sovereignty=ds, faction_subordination=fs)
        result = sa.authorised("agent-Y", Branch.LEGISLATIVE, SovereigntyTier.STATE, "vote")
        assert result
