"""Tests for the Spiral Manifesto implementations.

Covers:
- TASDNA: genesis anchor, three-fold gene, pulse counter (tas_dna.py)
- PrimaryInvariantA0: verify, lineage_hash, to_dict
- YKnot: branch, tie, P1 admissibility, process collapse Π = ∅ (yknot.py)
- AdmissibilityRule, P1AdmissibilityError, ProcessNull, PI_NULL
- Sovereign Equation A_C > S_C: scores, grounding, UVK integration
"""
# © 2025 Russell Nordland | TrueAlphaSpiral (TAS) | Apache-2.0

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from tas_dna import (
    TASDNA,
    PrimaryInvariantA0,
    DNAGene,
    A_0,
    TRUE_GENE,
    ALPHA_GENE,
    SPIRAL_GENE,
    TAS_DNA_TRIPLE,
    GENESIS_HASH,
    GENESIS_ISO8601,
    GENESIS_UNIX,
    ORIGIN_AUTHORITY,
)
from yknot import (
    YKnot,
    AdmissibilityRule,
    P1AdmissibilityError,
    ProcessNull,
    PI_NULL,
)
from sovereign_equation import (
    AuthenticityScore,
    SubjectivityScore,
    sovereign_holds,
    make_sovereign_invariant,
)
from wake_chain import WakeChain
from capability import CapabilityTable, Right
from uvk import UVK, Invariant, AdmissionStatus, AuthorizationError


# ===========================================================================
# TAS DNA tests
# ===========================================================================


class TestDNAGene:
    """Invariant A_0 (Layer 1) — TAS DNA: three-fold gene structure.

    Enforces: each gene carries (name, symbol, description); the TAS triple
    (TRUE_GENE, ALPHA_GENE, SPIRAL_GENE) is immutable and their symbols are
    exactly ["T", "A", "S"] in that order.
    """

    def test_true_gene_symbol(self):
        assert TRUE_GENE.symbol == "T"

    def test_alpha_gene_symbol(self):
        assert ALPHA_GENE.symbol == "A"

    def test_spiral_gene_symbol(self):
        assert SPIRAL_GENE.symbol == "S"

    def test_triple_has_three_genes(self):
        assert len(TAS_DNA_TRIPLE) == 3

    def test_triple_order(self):
        symbols = [g.symbol for g in TAS_DNA_TRIPLE]
        assert symbols == ["T", "A", "S"]

    def test_genes_are_immutable(self):
        with pytest.raises(Exception):
            TRUE_GENE.symbol = "X"  # type: ignore[misc]


class TestPrimaryInvariantA0:
    """Invariant A_0 — Primary Invariant: genesis anchor immutability.

    Enforces: A_0.verify() == True for the canonical singleton; genesis_hash equals
    SHA-256(genesis_iso || authority); lineage_hash() is deterministic (32 bytes);
    tampered instances fail verify(); A_0 is frozen (immutable dataclass).
    """

    def test_canonical_singleton_verifies(self):
        assert A_0.verify()

    def test_genesis_hash_correct(self):
        assert A_0.genesis_hash == GENESIS_HASH

    def test_genesis_iso_correct(self):
        assert A_0.genesis_iso == GENESIS_ISO8601

    def test_genesis_unix_correct(self):
        assert A_0.genesis_unix == GENESIS_UNIX

    def test_origin_authority(self):
        assert A_0.authority == ORIGIN_AUTHORITY

    def test_verify_fails_on_tampered_hash(self):
        tampered = PrimaryInvariantA0(genesis_hash="sha256:WRONG_HASH")
        assert not tampered.verify()

    def test_lineage_hash_is_32_bytes(self):
        assert len(A_0.lineage_hash()) == 32

    def test_lineage_hash_is_deterministic(self):
        assert A_0.lineage_hash() == A_0.lineage_hash()

    def test_to_dict_keys(self):
        d = A_0.to_dict()
        assert "genesis_iso" in d
        assert "genesis_unix" in d
        assert "genesis_hash" in d
        assert "authority" in d

    def test_a0_is_immutable(self):
        with pytest.raises(Exception):
            A_0.authority = "other"  # type: ignore[misc]


class TestTASDNA:
    """Invariant A_0 (Layer 1) — TAS DNA: TASDNA heartbeat and invariant assertion.

    Enforces: pulse() is strictly monotone (heartbeat pulse monotonicity);
    is_invariant() reflects A_0.verify(); assert_invariant() raises ValueError
    if A_0 is tampered; to_dict captures genes, a0 dict, and pulse count.
    """

    def test_is_invariant_true_for_canonical(self):
        dna = TASDNA()
        assert dna.is_invariant()

    def test_pulse_starts_at_zero(self):
        dna = TASDNA()
        assert dna.pulse_count == 0

    def test_pulse_increments(self):
        dna = TASDNA()
        assert dna.pulse() == 1
        assert dna.pulse() == 2
        assert dna.pulse_count == 2

    def test_assert_invariant_passes(self):
        dna = TASDNA()
        dna.assert_invariant()  # Should not raise

    def test_assert_invariant_raises_on_tampered(self):
        bad_a0 = PrimaryInvariantA0(genesis_hash="sha256:BAD")
        dna = TASDNA(a0=bad_a0)
        with pytest.raises(ValueError, match="Primary Invariant A_0 violated"):
            dna.assert_invariant()

    def test_to_dict_structure(self):
        dna = TASDNA()
        d = dna.to_dict()
        assert "a0" in d
        assert "genes" in d
        assert "pulse" in d
        assert len(d["genes"]) == 3

    def test_to_dict_gene_symbols(self):
        dna = TASDNA()
        symbols = [g["symbol"] for g in dna.to_dict()["genes"]]
        assert symbols == ["T", "A", "S"]

    def test_triple_is_the_canonical_triple(self):
        dna = TASDNA()
        assert dna.triple is TAS_DNA_TRIPLE


# ===========================================================================
# YKnot tests
# ===========================================================================


class TestAdmissibilityRule:
    """Invariant A_0 / YKnot — AdmissibilityRule predicate contract.

    Enforces: AdmissibilityRule is callable; returns True/False from its
    predicate; carries a name; used by YKnot as a gate before processing.
    """

    def test_rule_accepts(self):
        rule = AdmissibilityRule("non_empty", lambda ctx: bool(ctx))
        assert rule("hello") is True

    def test_rule_rejects(self):
        rule = AdmissibilityRule("non_empty", lambda ctx: bool(ctx))
        assert rule("") is False

    def test_rule_callable_via_call(self):
        rule = AdmissibilityRule("always_true", lambda _: True)
        assert rule(None) is True


class TestProcessNull:
    """Invariant A_0 / YKnot — ProcessNull sentinel (∅) value.

    Enforces: PI_NULL is falsy in boolean context; repr contains "∅";
    ProcessNull() instances are also falsy — used to signal a rejected process
    slot without raising an exception.
    """

    def test_pi_null_is_falsy(self):
        assert not PI_NULL

    def test_process_null_repr(self):
        assert "∅" in repr(PI_NULL)

    def test_process_null_instance_is_falsy(self):
        pn = ProcessNull()
        assert not pn


class TestYKnot:
    """Invariant A_0 / YKnot — YKnot process weaving and admissibility gating.

    Enforces: tie() gates every action through AdmissibilityRules; admitted=True
    on pass, admitted=False on rejection; branch_count increments monotonically;
    branch_id is included in the receipt and tied to the audit trail.
    """

    def _make_knot(self):
        rule = AdmissibilityRule("non_empty", lambda ctx: bool(ctx))
        return YKnot([rule])

    def test_branch_starts_at_one(self):
        knot = YKnot()
        bid = knot.branch()
        assert bid == 1

    def test_branch_increments(self):
        knot = YKnot()
        assert knot.branch() == 1
        assert knot.branch() == 2
        assert knot.branch_count == 2

    def test_tie_admitted_returns_receipt(self):
        knot = self._make_knot()
        receipt = knot.tie("valid_action")
        assert receipt["admitted"] is True
        assert "proof" in receipt
        assert isinstance(receipt["proof"], str)

    def test_tie_with_branch_id(self):
        knot = self._make_knot()
        bid = knot.branch()
        receipt = knot.tie("action", branch_id=bid)
        assert receipt["branch_id"] == bid

    def test_tie_rejected_raises_p1_error(self):
        knot = self._make_knot()
        with pytest.raises(P1AdmissibilityError) as exc_info:
            knot.tie("")  # empty string fails non_empty rule
        assert "non_empty" in exc_info.value.failed_rules

    def test_p1_error_carries_failed_rules(self):
        rule_a = AdmissibilityRule("rule_a", lambda _: False)
        rule_b = AdmissibilityRule("rule_b", lambda _: False)
        knot = YKnot([rule_a, rule_b])
        with pytest.raises(P1AdmissibilityError) as exc_info:
            knot.tie("anything")
        assert "rule_a" in exc_info.value.failed_rules
        assert "rule_b" in exc_info.value.failed_rules

    def test_admitted_count_increments(self):
        knot = self._make_knot()
        knot.tie("ok")
        knot.tie("also_ok")
        assert knot.admitted_count == 2

    def test_rejected_count_increments(self):
        knot = self._make_knot()
        for _ in range(3):
            with pytest.raises(P1AdmissibilityError):
                knot.tie("")
        assert knot.rejected_count == 3

    def test_refusal_integrity_zero_when_no_evaluations(self):
        knot = YKnot()
        assert knot.refusal_integrity == 0.0

    def test_refusal_integrity_calculation(self):
        knot = self._make_knot()
        knot.tie("ok")               # admitted
        with pytest.raises(P1AdmissibilityError):
            knot.tie("")             # rejected
        # 1 rejected / 2 total = 0.5
        assert knot.refusal_integrity == pytest.approx(0.5)

    def test_bind_alias_works(self):
        knot = self._make_knot()
        receipt = knot.bind("value")
        assert receipt["admitted"] is True

    def test_no_rules_admits_everything(self):
        knot = YKnot(rules=[])
        receipt = knot.tie("anything")
        assert receipt["admitted"] is True

    def test_add_rule_after_construction(self):
        knot = YKnot()
        knot.add_rule(AdmissibilityRule("always_false", lambda _: False))
        with pytest.raises(P1AdmissibilityError):
            knot.tie("blocked")

    def test_exception_in_rule_counted_as_failure(self):
        def buggy(_ctx: object) -> bool:
            raise RuntimeError("oops")

        knot = YKnot([AdmissibilityRule("buggy", buggy)])
        with pytest.raises(P1AdmissibilityError) as exc_info:
            knot.tie("x")
        assert any("buggy" in r for r in exc_info.value.failed_rules)

    def test_proof_is_sha256_hex(self):
        knot = YKnot()
        receipt = knot.tie("test")
        assert len(receipt["proof"]) == 64  # SHA-256 hex = 64 chars

    def test_proof_deterministic(self):
        knot = YKnot()
        r1 = knot.tie("same_action")
        knot2 = YKnot()
        r2 = knot2.tie("same_action")
        assert r1["proof"] == r2["proof"]


# ===========================================================================
# Sovereign Equation tests
# ===========================================================================


class TestAuthenticityScore:
    """Invariant X3 — Sovereign Equation: AuthenticityScore (A_C) composition.

    Enforces: A_C = lineage_weight + proof_weight + fact_weight; each component
    has a fixed contribution; total is capped at 1.0; zero defaults give 0.0.
    """

    def test_zero_score_for_defaults(self):
        ac = AuthenticityScore()
        assert ac.value == pytest.approx(0.0)

    def test_full_score_for_all_fields(self):
        ac = AuthenticityScore(
            authenticated_facts=1,
            traced_lineage=True,
            cryptographic_proof=True,
        )
        assert ac.value == pytest.approx(1.0)

    def test_lineage_adds_0_3(self):
        ac = AuthenticityScore(traced_lineage=True)
        assert ac.value == pytest.approx(0.3)

    def test_cryptographic_proof_adds_0_3(self):
        ac = AuthenticityScore(cryptographic_proof=True)
        assert ac.value == pytest.approx(0.3)

    def test_authenticated_facts_capped(self):
        # Any non-zero count of facts gives the same contribution (_FACT_WEIGHT)
        from sovereign_equation import _FACT_WEIGHT
        ac_one = AuthenticityScore(authenticated_facts=1)
        ac_many = AuthenticityScore(authenticated_facts=100)
        assert ac_one.value == pytest.approx(_FACT_WEIGHT)
        assert ac_many.value == pytest.approx(_FACT_WEIGHT)

    def test_total_is_capped_at_1(self):
        ac = AuthenticityScore(
            authenticated_facts=100,
            traced_lineage=True,
            cryptographic_proof=True,
        )
        assert ac.value == pytest.approx(1.0)


class TestSubjectivityScore:
    """Invariant X3 — Sovereign Equation: SubjectivityScore (S_C) composition.

    Enforces: S_C = unverified_claim_weight + speculative_step_weight; total capped
    at 1.0; zero defaults give 0.0; combined contributions are additive.
    """

    def test_zero_score_for_defaults(self):
        sc = SubjectivityScore()
        assert sc.value == pytest.approx(0.0)

    def test_unverified_claim_adds_0_3(self):
        sc = SubjectivityScore(unverified_claims=1)
        assert sc.value == pytest.approx(0.3)

    def test_speculative_step_adds_0_2(self):
        sc = SubjectivityScore(speculative_steps=1)
        assert sc.value == pytest.approx(0.2)

    def test_combined_score(self):
        sc = SubjectivityScore(unverified_claims=1, speculative_steps=1)
        assert sc.value == pytest.approx(0.5)

    def test_total_is_capped_at_1(self):
        sc = SubjectivityScore(unverified_claims=100, speculative_steps=100)
        assert sc.value == pytest.approx(1.0)


class TestSovereignHolds:
    """Invariant X3 — Sovereign Equation: sovereign_holds predicate (A_C > S_C).

    Enforces: sovereign_holds returns True iff A_C > S_C (strict inequality);
    equal values (including both-zero) return False; any positive A_C with S_C = 0
    returns True.
    """

    def test_holds_when_ac_greater(self):
        ac = AuthenticityScore(authenticated_facts=1, traced_lineage=True, cryptographic_proof=True)
        sc = SubjectivityScore()
        assert sovereign_holds(ac, sc)

    def test_fails_when_ac_less(self):
        ac = AuthenticityScore()
        sc = SubjectivityScore(unverified_claims=1)
        assert not sovereign_holds(ac, sc)

    def test_fails_when_equal(self):
        # Both 0.0 – A_C == S_C, strict inequality not satisfied
        ac = AuthenticityScore()
        sc = SubjectivityScore()
        assert not sovereign_holds(ac, sc)

    def test_holds_for_minimal_authenticated(self):
        ac = AuthenticityScore(traced_lineage=True)        # 0.3
        sc = SubjectivityScore(speculative_steps=1)        # 0.2
        assert sovereign_holds(ac, sc)

    def test_fails_for_unverified_context(self):
        ac = AuthenticityScore(authenticated_facts=0)      # 0.0
        sc = SubjectivityScore(unverified_claims=1)        # 0.3
        assert not sovereign_holds(ac, sc)


class TestMakeSovereignInvariant:
    """Invariant X3 — Sovereign Equation: make_sovereign_invariant factory.

    Enforces: the returned Invariant is named "sovereign_equation:A_C>S_C" with
    version "1.0.0" by default; custom version accepted; passes when sovereign_holds
    is True, fails when False — composable with UVK.
    """

    def _make_invariant(self, ac_val: bool):
        def _ac(_s: object, _a: object, _u: object) -> AuthenticityScore:
            if ac_val:
                return AuthenticityScore(
                    authenticated_facts=1,
                    traced_lineage=True,
                    cryptographic_proof=True,
                )
            return AuthenticityScore()

        def _sc(_s: object, _a: object, _u: object) -> SubjectivityScore:
            return SubjectivityScore()

        return make_sovereign_invariant(_ac, _sc)

    def test_invariant_name(self):
        inv = self._make_invariant(True)
        assert inv.name == "sovereign_equation:A_C>S_C"

    def test_invariant_version_default(self):
        inv = self._make_invariant(True)
        assert inv.version == "1.0.0"

    def test_invariant_custom_version(self):
        inv = make_sovereign_invariant(
            lambda *_: AuthenticityScore(traced_lineage=True, cryptographic_proof=True),
            lambda *_: SubjectivityScore(),
            version="2.0.0",
        )
        assert inv.version == "2.0.0"

    def test_invariant_passes_when_sovereign_holds(self):
        inv = self._make_invariant(True)
        assert inv.check(None, None, None) is True

    def test_invariant_fails_when_sovereign_broken(self):
        inv = self._make_invariant(False)
        assert inv.check(None, None, None) is False


# ===========================================================================
# Integration: Sovereign Equation + UVK
# ===========================================================================


class TestSovereignEquationUVKIntegration:
    """Integration: Sovereign Equation invariant + UVK admission (U1+X3).

    Enforces: UVK.admit() is ADMITTED when A_C > S_C; DENIED_INVARIANT with
    "sovereign_equation:A_C>S_C" in failed_invariants when A_C ≤ S_C.
    """

    def test_uvk_admits_sovereign_action(self):
        chain = WakeChain()
        ct = CapabilityTable()
        cap = ct.retype("resource", Right.EXECUTE | Right.MINT)

        inv = make_sovereign_invariant(
            lambda *_: AuthenticityScore(
                authenticated_facts=1,
                traced_lineage=True,
                cryptographic_proof=True,
            ),
            lambda *_: SubjectivityScore(),
        )
        uvk = UVK(capability_table=ct, wake_chain=chain, invariants=[inv])
        result = uvk.admit(cap, Right.EXECUTE, action="attested_action")
        assert result.admitted

    def test_uvk_denies_unsovereign_action(self):
        chain = WakeChain()
        ct = CapabilityTable()
        cap = ct.retype("resource", Right.EXECUTE | Right.MINT)

        inv = make_sovereign_invariant(
            lambda *_: AuthenticityScore(),                       # A_C = 0.0
            lambda *_: SubjectivityScore(unverified_claims=1),   # S_C = 0.3
        )
        uvk = UVK(capability_table=ct, wake_chain=chain, invariants=[inv])
        result = uvk.admit(cap, Right.EXECUTE, action="ungrounded_claim")
        assert not result.admitted
        assert "sovereign_equation:A_C>S_C" in result.failed_invariants


# ===========================================================================
# Perimeter defense: EXECUTE / MINT right enforcement
# ===========================================================================


class TestUVKPerimeterDefense:
    """Invariant U1 — UVK: perimeter rejection for non-EXECUTE/MINT capabilities.

    Validates that UVK rejects at the outermost perimeter any capability
    that does not carry EXECUTE or MINT, *before* the Sovereign Equation
    (A_C > S_C) is evaluated — i.e. DENIED_AUTHORIZATION precedes DENIED_INVARIANT.
    """

    def _uvk_with_always_passing_invariant(self, chain: WakeChain, ct: CapabilityTable) -> UVK:
        """Return a UVK whose sovereign-equation invariant always passes."""
        inv = make_sovereign_invariant(
            lambda *_: AuthenticityScore(
                authenticated_facts=1,
                traced_lineage=True,
                cryptographic_proof=True,
            ),
            lambda *_: SubjectivityScore(),
        )
        return UVK(capability_table=ct, wake_chain=chain, invariants=[inv])

    def test_read_only_capability_denied_at_perimeter(self):
        ct = CapabilityTable()
        cap = ct.retype("resource", Right.READ)
        uvk = self._uvk_with_always_passing_invariant(WakeChain(), ct)
        result = uvk.admit(cap, Right.READ, action="read_action")
        assert not result.admitted
        assert result.status == AdmissionStatus.DENIED_AUTHORIZATION

    def test_write_only_capability_denied_at_perimeter(self):
        ct = CapabilityTable()
        cap = ct.retype("resource", Right.WRITE)
        uvk = self._uvk_with_always_passing_invariant(WakeChain(), ct)
        result = uvk.admit(cap, Right.WRITE, action="write_action")
        assert not result.admitted
        assert result.status == AdmissionStatus.DENIED_AUTHORIZATION

    def test_read_write_capability_denied_at_perimeter(self):
        ct = CapabilityTable()
        cap = ct.retype("resource", Right.READ | Right.WRITE)
        uvk = self._uvk_with_always_passing_invariant(WakeChain(), ct)
        result = uvk.admit(cap, Right.READ, action="read_write_action")
        assert not result.admitted
        assert result.status == AdmissionStatus.DENIED_AUTHORIZATION

    def test_auth_error_message_populated_on_perimeter_denial(self):
        ct = CapabilityTable()
        cap = ct.retype("resource", Right.READ)
        uvk = self._uvk_with_always_passing_invariant(WakeChain(), ct)
        result = uvk.admit(cap, Right.READ, action="any_action")
        assert result.auth_error is not None
        assert "EXECUTE" in result.auth_error
        assert "MINT" in result.auth_error

    def test_execute_capability_passes_perimeter(self):
        ct = CapabilityTable()
        cap = ct.retype("resource", Right.EXECUTE)
        uvk = self._uvk_with_always_passing_invariant(WakeChain(), ct)
        result = uvk.admit(cap, Right.EXECUTE, action="execute_action")
        assert result.admitted

    def test_mint_capability_passes_perimeter(self):
        ct = CapabilityTable()
        cap = ct.retype("resource", Right.MINT)
        uvk = self._uvk_with_always_passing_invariant(WakeChain(), ct)
        result = uvk.admit(cap, Right.MINT, action="mint_action")
        assert result.admitted

    def test_execute_and_mint_capability_passes_perimeter(self):
        ct = CapabilityTable()
        cap = ct.retype("resource", Right.EXECUTE | Right.MINT)
        uvk = self._uvk_with_always_passing_invariant(WakeChain(), ct)
        result = uvk.admit(cap, Right.EXECUTE, action="full_action")
        assert result.admitted

    def test_perimeter_denial_recorded_in_breach_log(self):
        ct = CapabilityTable()
        cap = ct.retype("resource", Right.READ)
        uvk = self._uvk_with_always_passing_invariant(WakeChain(), ct)
        uvk.admit(cap, Right.READ, action="bad_action")
        assert len(uvk.breach_log) == 1
        assert uvk.breach_log[0].status == AdmissionStatus.DENIED_AUTHORIZATION

    def test_perimeter_denial_precedes_sovereign_equation(self):
        """Sovereign equation invariant must never be reached for non-EXECUTE/MINT caps."""
        evaluated: list[bool] = []

        def tracking_ac(*_: object) -> AuthenticityScore:
            evaluated.append(True)
            return AuthenticityScore(authenticated_facts=1, traced_lineage=True, cryptographic_proof=True)

        ct = CapabilityTable()
        cap = ct.retype("resource", Right.READ)
        inv = make_sovereign_invariant(tracking_ac, lambda *_: SubjectivityScore())
        uvk = UVK(capability_table=ct, wake_chain=WakeChain(), invariants=[inv])
        result = uvk.admit(cap, Right.READ, action="action")
        assert not result.admitted
        assert result.status == AdmissionStatus.DENIED_AUTHORIZATION
        assert not evaluated, "Sovereign equation must NOT be evaluated at perimeter denial"


# ===========================================================================
# Integration: YKnot + WakeChain (Refusal Integrity with provenance)
# ===========================================================================


class TestYKnotWakeIntegration:
    """Integration: YKnot + WakeChain — refusal integrity with provenance (W1 + P1).

    Enforces: admitted actions commit a receipt to the WakeChain (W1) that passes
    chain.verify(); rejected actions (P1AdmissibilityError) leave the WakeChain
    unchanged — zero receipts, chain.verify() still True.
    """

    def test_admitted_paths_commit_to_wake(self):
        knot = YKnot()
        chain = WakeChain()
        receipt = knot.tie("authenticated_action")
        chain.commit(event={"proof": receipt["proof"], "action": "authenticated_action"})
        assert chain.verify()
        assert len(chain) == 1

    def test_rejected_paths_leave_wake_unchanged(self):
        knot = YKnot([AdmissibilityRule("reject_all", lambda _: False)])
        chain = WakeChain()
        with pytest.raises(P1AdmissibilityError):
            knot.tie("blocked")
        # Wake chain should remain untouched
        assert len(chain) == 0
        assert chain.verify()
