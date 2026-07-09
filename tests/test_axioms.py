"""Tests for Governing Axioms P0 and P1.

Covers:
- AxiomViolation: attributes, message
- P0Equivalence: bind, validate, rebind guard, reflexive identity,
                 unknown symbols, registry_hash, bound_symbols
- P1Admissibility: add_clause, admit, rejection, counters, receipt fields
- AdmissibilityClause: callable behaviour
- AxiomSet: default factory, composition
- Integration: P0 + P1 in a combined pipeline
"""
# © 2025 Russell Nordland | TrueAlphaSpiral (TAS) | Apache-2.0

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from axioms import (
    AxiomViolation,
    P0Equivalence,
    P1Admissibility,
    AdmissibilityClause,
    AxiomSet,
)


# ===========================================================================
# AxiomViolation
# ===========================================================================


class TestAxiomViolation:
    """Axiom P0/P1 — AxiomViolation exception contract.

    Enforces: AxiomViolation carries the axiom name ("P0" or "P1") and a
    detail string, and is a subtype of Exception so callers can catch it
    at any governance boundary.
    """

    def test_axiom_stored(self):
        e = AxiomViolation("P0", "symbol drift")
        assert e.axiom == "P0"

    def test_detail_stored(self):
        e = AxiomViolation("P1", "clause failure")
        assert e.detail == "clause failure"

    def test_is_exception(self):
        assert isinstance(AxiomViolation("P0", "x"), Exception)

    def test_message_contains_axiom(self):
        e = AxiomViolation("P0", "drift detected")
        assert "P0" in str(e)

    def test_message_contains_detail(self):
        e = AxiomViolation("P1", "non_empty failed")
        assert "non_empty" in str(e)


# ===========================================================================
# P0Equivalence — bind
# ===========================================================================


class TestP0Bind:
    """Axiom P0 — Equivalence: symbol ≡ referent binding.

    Enforces: once symbol s is bound to referent r, re-binding to r' ≠ r
    raises AxiomViolation("P0", ...); re-binding to the same referent is
    idempotent; bound_symbols reflects all registered symbols.
    """

    def test_bind_single_symbol(self):
        p0 = P0Equivalence()
        p0.bind("four", 4)
        assert "four" in p0.bound_symbols

    def test_bind_multiple_symbols(self):
        p0 = P0Equivalence()
        p0.bind("one", 1)
        p0.bind("two", 2)
        assert "one" in p0.bound_symbols
        assert "two" in p0.bound_symbols

    def test_rebind_same_referent_is_idempotent(self):
        p0 = P0Equivalence()
        p0.bind("four", 4)
        p0.bind("four", 4)
        assert "four" in p0.bound_symbols

    def test_rebind_different_referent_raises(self):
        p0 = P0Equivalence()
        p0.bind("four", 4)
        with pytest.raises(AxiomViolation) as exc_info:
            p0.bind("four", 5)
        assert exc_info.value.axiom == "P0"

    def test_rebind_error_mentions_symbol(self):
        p0 = P0Equivalence()
        p0.bind("pi", 3)
        with pytest.raises(AxiomViolation) as exc_info:
            p0.bind("pi", 3.14)
        assert "pi" in exc_info.value.detail

    def test_string_and_numeric_referents(self):
        p0 = P0Equivalence()
        p0.bind("true", True)
        p0.bind("empty", "")
        assert "true" in p0.bound_symbols


# ===========================================================================
# P0Equivalence — validate
# ===========================================================================


class TestP0Validate:
    """Axiom P0 — Equivalence: symbol-referent drift detection.

    Enforces: validate(s, v) raises AxiomViolation("P0") when v ≠ r and v ≠ s
    (symbolic identity lock); validate passes for unregistered symbols and for
    the reflexive identity case v == s.
    """

    def test_registered_matching_referent_passes(self):
        p0 = P0Equivalence()
        p0.bind("four", 4)
        assert p0.validate("four", 4) is True

    def test_registered_wrong_referent_raises(self):
        p0 = P0Equivalence()
        p0.bind("four", 4)
        with pytest.raises(AxiomViolation) as exc_info:
            p0.validate("four", 5)
        assert exc_info.value.axiom == "P0"

    def test_unregistered_symbol_passes(self):
        p0 = P0Equivalence()
        assert p0.validate("unknown_symbol", 42) is True

    def test_reflexive_identity_passes(self):
        p0 = P0Equivalence()
        p0.bind("four", 4)
        assert p0.validate("four", "four") is True

    def test_drift_error_mentions_expected_and_observed(self):
        p0 = P0Equivalence()
        p0.bind("three", 3)
        with pytest.raises(AxiomViolation) as exc_info:
            p0.validate("three", 99)
        assert "3" in exc_info.value.detail or "three" in exc_info.value.detail

    def test_multiple_symbols_validated_independently(self):
        p0 = P0Equivalence()
        p0.bind("a", 1)
        p0.bind("b", 2)
        assert p0.validate("a", 1) is True
        assert p0.validate("b", 2) is True
        with pytest.raises(AxiomViolation):
            p0.validate("a", 2)


# ===========================================================================
# P0Equivalence — registry_hash and bound_symbols
# ===========================================================================


class TestP0RegistryHash:
    """Axiom P0 — Equivalence: registry_hash determinism.

    Enforces: registry_hash() is a deterministic SHA-256 over all (symbol, referent)
    pairs; identical bindings across independent instances produce identical hashes;
    hash changes after every new bind.
    """

    def test_empty_registry_has_stable_hash(self):
        p0 = P0Equivalence()
        h1 = p0.registry_hash()
        h2 = p0.registry_hash()
        assert h1 == h2

    def test_hash_changes_after_bind(self):
        p0 = P0Equivalence()
        h_before = p0.registry_hash()
        p0.bind("x", 10)
        h_after = p0.registry_hash()
        assert h_before != h_after

    def test_hash_is_64_hex(self):
        p0 = P0Equivalence()
        p0.bind("four", 4)
        h = p0.registry_hash()
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_same_bindings_same_hash(self):
        p0a = P0Equivalence()
        p0b = P0Equivalence()
        p0a.bind("x", 1)
        p0b.bind("x", 1)
        assert p0a.registry_hash() == p0b.registry_hash()

    def test_bound_symbols_empty_initially(self):
        p0 = P0Equivalence()
        assert p0.bound_symbols == []

    def test_bound_symbols_populated_after_bind(self):
        p0 = P0Equivalence()
        p0.bind("alpha", "A")
        p0.bind("beta", "B")
        syms = p0.bound_symbols
        assert "alpha" in syms
        assert "beta" in syms


# ===========================================================================
# AdmissibilityClause
# ===========================================================================


class TestAdmissibilityClause:
    """Axiom P1 — Admissibility: clause predicate contract.

    Enforces: AdmissibilityClause is callable; returns True/False from its
    check function; carries a name; forwards the proof argument to the check.
    """

    def test_callable_returns_true_when_check_passes(self):
        clause = AdmissibilityClause("non_empty", lambda t, _: bool(t))
        assert clause("some_action", None) is True

    def test_callable_returns_false_when_check_fails(self):
        clause = AdmissibilityClause("non_empty", lambda t, _: bool(t))
        assert clause("", None) is False

    def test_name_stored(self):
        clause = AdmissibilityClause("my_rule", lambda t, p: True)
        assert clause.name == "my_rule"

    def test_proof_passed_to_check(self):
        received = []
        def check(t, p):
            received.append(p)
            return True
        clause = AdmissibilityClause("proof_check", check)
        clause("action", "my_proof")
        assert received == ["my_proof"]


# ===========================================================================
# P1Admissibility — admit
# ===========================================================================


class TestP1Admit:
    """Axiom P1 — Admissibility: transition admission gate.

    Enforces: V(spec, proof, π) = True iff all AdmissibilityClause predicates
    return True; failure raises AxiomViolation("P1"); transition_hash in the
    receipt is the deterministic SHA-256 of the canonical-JSON transition.
    """

    def _non_empty_p1(self):
        p1 = P1Admissibility()
        p1.add_clause(AdmissibilityClause("non_empty", lambda t, _: bool(t)))
        return p1

    def test_no_clauses_admits_anything(self):
        p1 = P1Admissibility()
        receipt = p1.admit("anything")
        assert receipt["admitted"] is True

    def test_passing_clause_returns_receipt(self):
        p1 = self._non_empty_p1()
        receipt = p1.admit("valid_action")
        assert receipt["admitted"] is True

    def test_failing_clause_raises_axiom_violation(self):
        p1 = self._non_empty_p1()
        with pytest.raises(AxiomViolation) as exc_info:
            p1.admit("")
        assert exc_info.value.axiom == "P1"

    def test_failing_clause_names_in_detail(self):
        p1 = P1Admissibility()
        p1.add_clause(AdmissibilityClause("must_be_dict", lambda t, _: isinstance(t, dict)))
        with pytest.raises(AxiomViolation) as exc_info:
            p1.admit("not_a_dict")
        assert "must_be_dict" in exc_info.value.detail

    def test_receipt_contains_transition_hash(self):
        p1 = P1Admissibility()
        receipt = p1.admit({"op": "read"})
        assert "transition_hash" in receipt
        assert len(receipt["transition_hash"]) == 64

    def test_receipt_failed_clauses_empty_on_success(self):
        p1 = P1Admissibility()
        receipt = p1.admit("valid")
        assert receipt["failed_clauses"] == []

    def test_transition_hash_deterministic(self):
        p1 = P1Admissibility()
        r1 = p1.admit({"op": "write"})
        r2 = p1.admit({"op": "write"})
        assert r1["transition_hash"] == r2["transition_hash"]

    def test_different_transitions_different_hashes(self):
        p1 = P1Admissibility()
        r1 = p1.admit({"op": "read"})
        r2 = p1.admit({"op": "write"})
        assert r1["transition_hash"] != r2["transition_hash"]

    def test_multiple_clauses_all_must_pass(self):
        p1 = P1Admissibility()
        p1.add_clause(AdmissibilityClause("is_dict", lambda t, _: isinstance(t, dict)))
        p1.add_clause(AdmissibilityClause("has_op", lambda t, _: "op" in t))
        p1.admit({"op": "read"})

        with pytest.raises(AxiomViolation):
            p1.admit({"not_op": "x"})


# ===========================================================================
# P1Admissibility — counters
# ===========================================================================


class TestP1Counters:
    """Axiom P1 — Admissibility: admission/rejection counters.

    Enforces: admitted_count increments on each successful admit;
    rejected_count increments on each AxiomViolation; neither counter
    pollutes the other; both start at zero.
    """

    def test_admitted_count_increments(self):
        p1 = P1Admissibility()
        p1.admit("a")
        p1.admit("b")
        assert p1.admitted_count == 2

    def test_rejected_count_increments(self):
        p1 = P1Admissibility()
        p1.add_clause(AdmissibilityClause("non_empty", lambda t, _: bool(t)))
        with pytest.raises(AxiomViolation):
            p1.admit("")
        assert p1.rejected_count == 1

    def test_counters_start_at_zero(self):
        p1 = P1Admissibility()
        assert p1.admitted_count == 0
        assert p1.rejected_count == 0

    def test_rejection_does_not_increment_admitted(self):
        p1 = P1Admissibility()
        p1.add_clause(AdmissibilityClause("always_false", lambda t, _: False))
        with pytest.raises(AxiomViolation):
            p1.admit("x")
        assert p1.admitted_count == 0

    def test_mixed_admits_and_rejections(self):
        p1 = P1Admissibility()
        p1.add_clause(AdmissibilityClause("non_empty", lambda t, _: bool(t)))
        p1.admit("valid")
        with pytest.raises(AxiomViolation):
            p1.admit("")
        p1.admit("also_valid")
        assert p1.admitted_count == 2
        assert p1.rejected_count == 1


# ===========================================================================
# AxiomSet
# ===========================================================================


class TestAxiomSet:
    """Axioms P0+P1 — AxiomSet: default factory and composition.

    Enforces: AxiomSet.default() produces an independent P0Equivalence and
    P1Admissibility instance with no initial bindings or clauses; version
    defaults are set; P0 and P1 are independent of each other.
    """

    def test_default_creates_p0_and_p1(self):
        axioms = AxiomSet.default()
        assert isinstance(axioms.p0, P0Equivalence)
        assert isinstance(axioms.p1, P1Admissibility)

    def test_default_p0_has_no_bindings(self):
        axioms = AxiomSet.default()
        assert axioms.p0.bound_symbols == []

    def test_default_p1_admits_anything(self):
        axioms = AxiomSet.default()
        receipt = axioms.p1.admit("any_transition")
        assert receipt["admitted"] is True

    def test_p0_and_p1_are_independent(self):
        axioms = AxiomSet.default()
        axioms.p0.bind("four", 4)
        axioms.p1.add_clause(AdmissibilityClause("non_empty", lambda t, _: bool(t)))
        assert "four" in axioms.p0.bound_symbols
        assert axioms.p1.admitted_count == 0


# ===========================================================================
# Integration: combined P0 + P1 pipeline
# ===========================================================================


class TestAxiomsIntegration:
    """Integration: P0 Equivalence + P1 Admissibility pipeline.

    Enforces: P0 drift detection blocks the pipeline before P1 is reached;
    P1 rejection is independent of P0 state; registry_hash can be committed
    into a P1 transition to create a cross-axiom cryptographic binding.
    """

    def test_p0_and_p1_cooperate(self):
        axioms = AxiomSet.default()
        axioms.p0.bind("four", 4)
        axioms.p1.add_clause(
            AdmissibilityClause("identity_check",
                lambda t, _: t.get("value") == axioms.p0._registry.get(t.get("symbol")))
        )
        transition = {"symbol": "four", "value": 4}
        axioms.p0.validate("four", 4)
        receipt = axioms.p1.admit(transition)
        assert receipt["admitted"] is True

    def test_p0_drift_blocks_before_p1(self):
        axioms = AxiomSet.default()
        axioms.p0.bind("four", 4)
        with pytest.raises(AxiomViolation) as exc_info:
            axioms.p0.validate("four", 999)
        assert exc_info.value.axiom == "P0"

    def test_p1_rejection_independent_of_p0(self):
        axioms = AxiomSet.default()
        axioms.p0.bind("a", 1)
        axioms.p1.add_clause(AdmissibilityClause("must_have_key",
                                                  lambda t, _: "key" in t))
        axioms.p0.validate("a", 1)
        with pytest.raises(AxiomViolation) as exc_info:
            axioms.p1.admit({"no_key": "value"})
        assert exc_info.value.axiom == "P1"

    def test_registry_hash_committed_before_transition(self):
        axioms = AxiomSet.default()
        axioms.p0.bind("x", 42)
        h = axioms.p0.registry_hash()
        receipt = axioms.p1.admit({"registry_hash": h})
        assert receipt["admitted"] is True

    def test_version_defaults_stored(self):
        axioms = AxiomSet.default()
        assert axioms.p0.version == "1.0.0"
        assert axioms.p1.version == "1.0.0"
