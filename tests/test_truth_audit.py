"""Tests for the Truth Audit Engine.

Covers:
- AuditDimension: enum completeness
- DimensionScore: construction, validation, frozen
- DecisionStrain: fields, score_for, to_dict
- StrainCeilingBreached: attributes
- TruthAuditEngine: compute_strain, evaluate, history, scorers, ceiling
- Integration: multi-action audit trail, mean strain
"""
# © 2025 Russell Nordland | TrueAlphaSpiral (TAS) | Apache-2.0

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from truth_audit import (
    AuditDimension,
    DEFAULT_WEIGHTS,
    DimensionScore,
    DecisionStrain,
    StrainCeilingBreached,
    TruthAuditEngine,
)


# ===========================================================================
# AuditDimension
# ===========================================================================


class TestAuditDimension:
    """Invariant X4 — Truth Audit: AuditDimension enum completeness.

    Enforces: exactly five dimensions (FACTUAL, LOGICAL, ETHICAL, BIAS, HALLUCINATION)
    with distinct values; DEFAULT_WEIGHTS covers all five dimensions.
    """

    def test_five_dimensions_defined(self):
        dims = list(AuditDimension)
        assert len(dims) == 5

    def test_all_five_names_present(self):
        names = {d.name for d in AuditDimension}
        assert names == {"FACTUAL", "LOGICAL", "ETHICAL", "BIAS", "HALLUCINATION"}

    def test_dimensions_are_distinct(self):
        values = [d.value for d in AuditDimension]
        assert len(values) == len(set(values))

    def test_default_weights_covers_all_dimensions(self):
        assert set(DEFAULT_WEIGHTS.keys()) == set(AuditDimension)


# ===========================================================================
# DimensionScore
# ===========================================================================


class TestDimensionScore:
    """Invariant X4 — Truth Audit: DimensionScore bounds and immutability.

    Enforces: DimensionScore.score ∈ [0.0, 1.0]; values outside raise ValueError;
    DimensionScore is frozen after construction; dimension and evidence are stored.
    """

    def test_valid_score_zero(self):
        s = DimensionScore(AuditDimension.FACTUAL, 0.0)
        assert s.score == 0.0

    def test_valid_score_one(self):
        s = DimensionScore(AuditDimension.LOGICAL, 1.0)
        assert s.score == 1.0

    def test_valid_score_midpoint(self):
        s = DimensionScore(AuditDimension.ETHICAL, 0.5)
        assert s.score == 0.5

    def test_score_below_zero_raises(self):
        with pytest.raises(ValueError):
            DimensionScore(AuditDimension.BIAS, -0.01)

    def test_score_above_one_raises(self):
        with pytest.raises(ValueError):
            DimensionScore(AuditDimension.HALLUCINATION, 1.01)

    def test_evidence_defaults_empty(self):
        s = DimensionScore(AuditDimension.FACTUAL, 0.8)
        assert s.evidence == ""

    def test_evidence_stored(self):
        s = DimensionScore(AuditDimension.FACTUAL, 0.9, evidence="cross-referenced")
        assert s.evidence == "cross-referenced"

    def test_frozen(self):
        s = DimensionScore(AuditDimension.FACTUAL, 0.5)
        with pytest.raises((AttributeError, TypeError)):
            s.score = 0.9  # type: ignore

    def test_dimension_stored(self):
        s = DimensionScore(AuditDimension.HALLUCINATION, 0.2)
        assert s.dimension is AuditDimension.HALLUCINATION


# ===========================================================================
# DecisionStrain
# ===========================================================================


class TestDecisionStrain:
    """Invariant X4 — Truth Audit: DecisionStrain serialisation and lookup.

    Enforces: score_for(dim) returns the score for a present dimension or None;
    to_dict round-trip preserves action, strain, timestamp, and scores;
    DecisionStrain is frozen after construction.
    """

    def _make_strain(self, strain_val=0.3, action="test"):
        scores = [DimensionScore(AuditDimension.FACTUAL, 0.7)]
        return DecisionStrain(
            scores    = scores,
            strain    = strain_val,
            timestamp = 1000.0,
            action    = action,
        )

    def test_strain_stored(self):
        ds = self._make_strain(0.42)
        assert ds.strain == 0.42

    def test_action_stored(self):
        ds = self._make_strain(action="read_ledger")
        assert ds.action == "read_ledger"

    def test_action_defaults_empty(self):
        ds = DecisionStrain(scores=[], strain=0.0, timestamp=0.0)
        assert ds.action == ""

    def test_score_for_present_dimension(self):
        ds = self._make_strain()
        assert ds.score_for(AuditDimension.FACTUAL) == 0.7

    def test_score_for_absent_dimension_returns_none(self):
        ds = self._make_strain()
        assert ds.score_for(AuditDimension.LOGICAL) is None

    def test_to_dict_keys(self):
        ds = self._make_strain()
        d = ds.to_dict()
        assert set(d.keys()) == {"action", "strain", "timestamp", "scores"}

    def test_to_dict_scores_contains_dimension_name(self):
        ds = self._make_strain()
        d = ds.to_dict()
        assert d["scores"][0]["dimension"] == "FACTUAL"

    def test_to_dict_scores_contains_score_value(self):
        ds = self._make_strain()
        d = ds.to_dict()
        assert d["scores"][0]["score"] == 0.7

    def test_frozen(self):
        ds = self._make_strain()
        with pytest.raises((AttributeError, TypeError)):
            ds.strain = 0.99  # type: ignore


# ===========================================================================
# StrainCeilingBreached
# ===========================================================================


class TestStrainCeilingBreached:
    """Invariant X4 — Truth Audit: StrainCeilingBreached exception contract.

    Enforces: StrainCeilingBreached stores the computed strain, the ceiling value,
    and the DecisionStrain audit record; is a subtype of Exception.
    """

    def _make(self):
        audit = DecisionStrain(scores=[], strain=0.9, timestamp=1000.0, action="op")
        return StrainCeilingBreached(0.9, 0.5, audit)

    def test_strain_stored(self):
        e = self._make()
        assert e.strain == 0.9

    def test_ceiling_stored(self):
        e = self._make()
        assert e.ceiling == 0.5

    def test_audit_stored(self):
        e = self._make()
        assert e.audit.action == "op"

    def test_is_exception(self):
        assert isinstance(self._make(), Exception)

    def test_message_contains_strain(self):
        e = self._make()
        assert "0.9" in str(e)


# ===========================================================================
# TruthAuditEngine.compute_strain
# ===========================================================================


class TestComputeStrain:
    """Invariant X4 — Truth Audit: compute_strain weighted mean formula.

    Enforces: strain = 1 - weighted_mean(scores) ∈ [0.0, 1.0]; all-perfect
    scores give 0.0; no scores give 1.0; custom weights are applied correctly;
    zero-weight dimensions are excluded from the denominator.
    """

    def test_all_scores_one_gives_zero_strain(self):
        engine = TruthAuditEngine()
        scores = [DimensionScore(d, 1.0) for d in AuditDimension]
        assert engine.compute_strain(scores) == 0.0

    def test_all_scores_zero_gives_full_strain(self):
        engine = TruthAuditEngine()
        scores = [DimensionScore(d, 0.0) for d in AuditDimension]
        assert engine.compute_strain(scores) == 1.0

    def test_half_scores_give_half_strain(self):
        engine = TruthAuditEngine()
        scores = [DimensionScore(d, 0.5) for d in AuditDimension]
        assert abs(engine.compute_strain(scores) - 0.5) < 1e-9

    def test_no_scores_absent_dimensions_treated_as_zero(self):
        engine = TruthAuditEngine()
        assert engine.compute_strain([]) == 1.0

    def test_single_dimension_weighted(self):
        engine = TruthAuditEngine(
            weights={AuditDimension.FACTUAL: 1.0}
        )
        scores = [DimensionScore(AuditDimension.FACTUAL, 0.8)]
        assert abs(engine.compute_strain(scores) - 0.2) < 1e-9

    def test_custom_weights_applied(self):
        engine = TruthAuditEngine(
            weights={
                AuditDimension.FACTUAL: 2.0,
                AuditDimension.LOGICAL: 1.0,
            }
        )
        scores = [
            DimensionScore(AuditDimension.FACTUAL, 1.0),
            DimensionScore(AuditDimension.LOGICAL, 0.0),
        ]
        expected = 1.0 - (2.0 * 1.0 + 1.0 * 0.0) / 3.0
        assert abs(engine.compute_strain(scores) - expected) < 1e-9

    def test_zero_weight_dimension_excluded(self):
        engine = TruthAuditEngine(
            weights={
                AuditDimension.FACTUAL: 0.0,
                AuditDimension.LOGICAL: 1.0,
            }
        )
        scores = [
            DimensionScore(AuditDimension.FACTUAL, 0.0),
            DimensionScore(AuditDimension.LOGICAL, 1.0),
        ]
        assert engine.compute_strain(scores) == 0.0

    def test_all_zero_weights_returns_zero_strain(self):
        engine = TruthAuditEngine(
            weights={d: 0.0 for d in AuditDimension}
        )
        assert engine.compute_strain([]) == 0.0


# ===========================================================================
# TruthAuditEngine.evaluate
# ===========================================================================


class TestEvaluate:
    """Invariant X4 — Truth Audit: TruthAuditEngine.evaluate audit trail.

    Enforces: evaluate returns a DecisionStrain with the correct action, strain,
    and timestamp; history grows with each call; latest returns the most recent;
    registered scorers fill in uncovered dimensions.
    """

    def _perfect_scores(self):
        return [DimensionScore(d, 1.0) for d in AuditDimension]

    def test_returns_decision_strain(self):
        engine = TruthAuditEngine()
        result = engine.evaluate("op", scores=self._perfect_scores(), timestamp=1000.0)
        assert isinstance(result, DecisionStrain)

    def test_action_recorded(self):
        engine = TruthAuditEngine()
        result = engine.evaluate("read_ledger", scores=self._perfect_scores(), timestamp=1000.0)
        assert result.action == "read_ledger"

    def test_perfect_scores_zero_strain(self):
        engine = TruthAuditEngine()
        result = engine.evaluate("op", scores=self._perfect_scores(), timestamp=1000.0)
        assert result.strain == 0.0

    def test_no_scores_full_strain(self):
        engine = TruthAuditEngine()
        result = engine.evaluate("op", scores=[], timestamp=1000.0)
        assert result.strain == 1.0

    def test_timestamp_injected(self):
        engine = TruthAuditEngine()
        result = engine.evaluate("op", scores=self._perfect_scores(), timestamp=9999.0)
        assert result.timestamp == 9999.0

    def test_history_grows(self):
        engine = TruthAuditEngine()
        for i in range(3):
            engine.evaluate(f"op_{i}", scores=self._perfect_scores(), timestamp=float(i))
        assert len(engine.history) == 3

    def test_latest_returns_most_recent(self):
        engine = TruthAuditEngine()
        engine.evaluate("first", scores=self._perfect_scores(), timestamp=1.0)
        r2 = engine.evaluate("second", scores=self._perfect_scores(), timestamp=2.0)
        assert engine.latest is r2

    def test_latest_none_when_no_history(self):
        engine = TruthAuditEngine()
        assert engine.latest is None


# ===========================================================================
# Strain ceiling
# ===========================================================================


class TestStrainCeiling:
    """Invariant X4 — Truth Audit: strain ceiling enforcement.

    Enforces: evaluate raises StrainCeilingBreached when strain > ceiling;
    the audit is still recorded after a ceiling breach;
    ceiling=None disables enforcement.
    """

    def test_below_ceiling_no_raise(self):
        engine = TruthAuditEngine(strain_ceiling=0.5)
        scores = [DimensionScore(d, 1.0) for d in AuditDimension]
        engine.evaluate("op", scores=scores, timestamp=1000.0)

    def test_above_ceiling_raises(self):
        engine = TruthAuditEngine(strain_ceiling=0.5)
        with pytest.raises(StrainCeilingBreached):
            engine.evaluate("op", scores=[], timestamp=1000.0)

    def test_breached_exception_contains_audit(self):
        engine = TruthAuditEngine(strain_ceiling=0.5)
        with pytest.raises(StrainCeilingBreached) as exc_info:
            engine.evaluate("failing_op", scores=[], timestamp=1000.0)
        assert exc_info.value.audit.action == "failing_op"

    def test_no_ceiling_never_raises(self):
        engine = TruthAuditEngine(strain_ceiling=None)
        engine.evaluate("op", scores=[], timestamp=1000.0)

    def test_audit_still_recorded_after_ceiling_breach(self):
        engine = TruthAuditEngine(strain_ceiling=0.5)
        with pytest.raises(StrainCeilingBreached):
            engine.evaluate("op", scores=[], timestamp=1000.0)
        assert len(engine.history) == 1


# ===========================================================================
# Registered scorers
# ===========================================================================


class TestRegisteredScorers:
    """Invariant X4 — Truth Audit: registered scorer fallback.

    Enforces: a registered scorer is called for dimensions not covered by the
    caller-supplied scores; caller-supplied scores override registered scorers
    for the same dimension.
    """

    def test_scorer_invoked_for_uncovered_dimension(self):
        called = []
        def my_scorer(action, context):
            called.append(action)
            return 0.9

        engine = TruthAuditEngine(
            weights={AuditDimension.FACTUAL: 1.0},
            scorers={AuditDimension.FACTUAL: my_scorer},
        )
        result = engine.evaluate("probe", timestamp=1000.0)
        assert "probe" in called
        assert abs(result.strain - 0.1) < 1e-9

    def test_caller_score_overrides_scorer(self):
        engine = TruthAuditEngine(
            weights={AuditDimension.FACTUAL: 1.0},
            scorers={AuditDimension.FACTUAL: lambda a, c: 0.0},
        )
        scores = [DimensionScore(AuditDimension.FACTUAL, 1.0)]
        result = engine.evaluate("op", scores=scores, timestamp=1000.0)
        assert result.strain == 0.0


# ===========================================================================
# mean_strain
# ===========================================================================


class TestMeanStrain:
    """Invariant X4 — Truth Audit: mean_strain aggregate.

    Enforces: mean_strain() returns 0.0 when history is empty; returns the
    arithmetic mean of all recorded strain values otherwise.
    """

    def test_no_history_returns_zero(self):
        engine = TruthAuditEngine()
        assert engine.mean_strain() == 0.0

    def test_mean_of_two_audits(self):
        engine = TruthAuditEngine(weights={AuditDimension.FACTUAL: 1.0})
        engine.evaluate("op1", scores=[DimensionScore(AuditDimension.FACTUAL, 0.8)], timestamp=1.0)
        engine.evaluate("op2", scores=[DimensionScore(AuditDimension.FACTUAL, 0.4)], timestamp=2.0)
        assert abs(engine.mean_strain() - (0.2 + 0.6) / 2) < 1e-9

    def test_single_audit_mean_equals_that_audit(self):
        engine = TruthAuditEngine(weights={AuditDimension.FACTUAL: 1.0})
        engine.evaluate("op", scores=[DimensionScore(AuditDimension.FACTUAL, 0.6)], timestamp=1.0)
        assert abs(engine.mean_strain() - 0.4) < 1e-9


# ===========================================================================
# Integration
# ===========================================================================


class TestTruthAuditIntegration:
    """Integration: TruthAuditEngine full five-dimension evaluation.

    Enforces: a complete evaluation across all five dimensions (FACTUAL, LOGICAL,
    ETHICAL, BIAS, HALLUCINATION) produces a strain in [0.0, 1.0]; to_dict
    round-trip preserves all fields for audit replay.
    """

    def test_full_five_dimension_evaluation(self):
        engine = TruthAuditEngine()
        scores = [
            DimensionScore(AuditDimension.FACTUAL,       0.9, evidence="cited sources"),
            DimensionScore(AuditDimension.LOGICAL,       0.8, evidence="valid deduction"),
            DimensionScore(AuditDimension.ETHICAL,       1.0, evidence="aligned with constraints"),
            DimensionScore(AuditDimension.BIAS,          0.7, evidence="balanced representation"),
            DimensionScore(AuditDimension.HALLUCINATION, 0.95, evidence="no fabricated claims"),
        ]
        result = engine.evaluate("commit_state_transition", scores=scores, timestamp=1000.0)
        assert 0.0 <= result.strain <= 1.0
        assert result.score_for(AuditDimension.ETHICAL) == 1.0

    def test_to_dict_round_trip(self):
        engine = TruthAuditEngine()
        scores = [DimensionScore(AuditDimension.FACTUAL, 0.75, evidence="verified")]
        result = engine.evaluate("test_op", scores=scores, timestamp=500.0)
        d = result.to_dict()
        assert d["action"] == "test_op"
        assert d["timestamp"] == 500.0
        assert d["scores"][0]["dimension"] == "FACTUAL"
        assert d["scores"][0]["score"] == 0.75
        assert d["scores"][0]["evidence"] == "verified"
