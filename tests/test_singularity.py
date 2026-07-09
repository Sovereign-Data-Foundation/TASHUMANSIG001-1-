"""
Tests for singularity.py — Recursive Contextualization of the Mathematical Singularity

Verifies:
  1. FixedPoint.at() — correct analytical formula, stability, derivative
  2. SingularityContext.converge() — orbital convergence to x*
  3. SingularityContext.prove_boundary() — self-referential proof record
  4. recursive_contextualize() — four-layer recursive structure
  5. orbit_stream() — infinite iterator behavior

STAMP_ANCHOR_2026_07_07
"""

import math

import pytest

from singularity import (
    DEFAULT_EPSILON,
    INERT_CONSTANT,
    R_BOUNDARY,
    ConvergenceTrace,
    FixedPoint,
    SingularityContext,
    recursive_contextualize,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

class TestConstants:
    def test_r_boundary_is_2_4(self):
        assert R_BOUNDARY == pytest.approx(2.4)

    def test_inert_constant_is_7_over_12(self):
        assert INERT_CONSTANT == pytest.approx(7 / 12, abs=1e-15)

    def test_inert_constant_is_fixed_point_at_boundary(self):
        """7/12 = 1 - 1/2.4: the inert constant IS the fixed point at r=2.4."""
        assert INERT_CONSTANT == pytest.approx(1.0 - 1.0 / R_BOUNDARY, abs=1e-15)

    def test_inert_constant_satisfies_fixed_point_equation(self):
        """f(x*) = r·x*·(1-x*) must equal x*."""
        x = INERT_CONSTANT
        f_x = R_BOUNDARY * x * (1.0 - x)
        assert f_x == pytest.approx(x, abs=1e-14)


# ---------------------------------------------------------------------------
# FixedPoint
# ---------------------------------------------------------------------------

class TestFixedPoint:
    def test_at_boundary_returns_7_over_12(self):
        fp = FixedPoint.at(R_BOUNDARY)
        assert fp.value == pytest.approx(7 / 12, abs=1e-14)

    def test_formula_x_star_equals_1_minus_1_over_r(self):
        for r in [1.5, 2.0, 2.4, 2.9]:
            fp = FixedPoint.at(r)
            assert fp.value == pytest.approx(1.0 - 1.0 / r, abs=1e-14)

    def test_derivative_at_fixed_point_is_2_minus_r(self):
        for r in [1.5, 2.0, 2.4, 2.9]:
            fp = FixedPoint.at(r)
            assert fp.derivative_at_fixed_point == pytest.approx(2.0 - r, abs=1e-14)

    def test_stability_for_r_in_1_to_3(self):
        for r in [1.1, 1.5, 2.0, 2.4, 2.9]:
            fp = FixedPoint.at(r)
            assert fp.is_stable is True

    def test_instability_for_r_equal_3(self):
        fp = FixedPoint.at(3.0)
        assert fp.is_stable is False  # |2 - 3| = 1, not strictly < 1

    def test_instability_for_r_above_3(self):
        fp = FixedPoint.at(3.5)
        assert fp.is_stable is False

    def test_boundary_fixed_point_is_stable(self):
        fp = FixedPoint.at(R_BOUNDARY)
        assert fp.is_stable is True

    def test_boundary_contraction_constant(self):
        fp = FixedPoint.at(R_BOUNDARY)
        assert abs(fp.derivative_at_fixed_point) == pytest.approx(abs(2.0 - R_BOUNDARY))
        assert abs(fp.derivative_at_fixed_point) < 1.0

    def test_frozen(self):
        fp = FixedPoint.at(2.0)
        with pytest.raises((AttributeError, TypeError)):
            fp.value = 0.0  # type: ignore[misc]

    def test_r_stored_correctly(self):
        fp = FixedPoint.at(2.4)
        assert fp.r == pytest.approx(2.4)

    def test_r_le_1_returns_zero_fixed_point(self):
        fp = FixedPoint.at(0.5)
        assert fp.value == pytest.approx(0.0)

    def test_r_exactly_1_returns_zero_fixed_point(self):
        fp = FixedPoint.at(1.0)
        assert fp.value == pytest.approx(0.0)

    def test_negative_r_raises(self):
        with pytest.raises(ValueError):
            FixedPoint.at(-1.0)

    def test_zero_r_raises(self):
        with pytest.raises(ValueError):
            FixedPoint.at(0.0)


# ---------------------------------------------------------------------------
# SingularityContext.converge
# ---------------------------------------------------------------------------

class TestConverge:
    def test_converges_from_below_x_star(self):
        ctx = SingularityContext()
        trace = ctx.converge(0.1, R_BOUNDARY)
        assert trace.converged is True

    def test_converges_from_above_x_star(self):
        ctx = SingularityContext()
        trace = ctx.converge(0.9, R_BOUNDARY)
        assert trace.converged is True

    def test_converges_from_near_x_star(self):
        ctx = SingularityContext()
        trace = ctx.converge(0.5, R_BOUNDARY)
        assert trace.converged is True

    def test_orbit_ends_near_fixed_point(self):
        ctx = SingularityContext(epsilon=1e-9)
        trace = ctx.converge(0.3, R_BOUNDARY)
        assert abs(trace.orbit[-1] - INERT_CONSTANT) < 1e-6

    def test_residual_below_epsilon(self):
        ctx = SingularityContext(epsilon=1e-9)
        trace = ctx.converge(0.3, R_BOUNDARY)
        assert trace.residual < 1e-9

    def test_orbit_starts_at_x_initial(self):
        ctx = SingularityContext()
        trace = ctx.converge(0.42, R_BOUNDARY)
        assert trace.orbit[0] == pytest.approx(0.42)

    def test_trace_records_r(self):
        ctx = SingularityContext()
        trace = ctx.converge(0.5, 2.0)
        assert trace.r == pytest.approx(2.0)

    def test_trace_records_x_initial(self):
        ctx = SingularityContext()
        trace = ctx.converge(0.7, 2.0)
        assert trace.x_initial == pytest.approx(0.7)

    def test_iterations_positive_on_convergence(self):
        ctx = SingularityContext()
        trace = ctx.converge(0.5, R_BOUNDARY)
        assert trace.iterations > 0

    def test_chaotic_r_does_not_converge(self):
        ctx = SingularityContext(max_iter=500)
        trace = ctx.converge(0.4, 3.9)
        assert trace.converged is False

    def test_convergence_rate_follows_contraction_constant(self):
        """Convergence rate is governed by L=|2-r|. r=2.39 → L=0.39, r=1.5 → L=0.5.
        So r=2.39 converges faster (fewer iterations) than r=1.5 from the same start."""
        ctx = SingularityContext(epsilon=1e-9)
        faster = ctx.converge(0.5, 2.39)  # L = 0.39
        slower = ctx.converge(0.5, 1.5)   # L = 0.50
        assert faster.iterations <= slower.iterations

    def test_convergence_trace_is_correct_type(self):
        ctx = SingularityContext()
        trace = ctx.converge(0.5, R_BOUNDARY)
        assert isinstance(trace, ConvergenceTrace)

    def test_all_orbit_steps_apply_logistic_map(self):
        ctx = SingularityContext()
        trace = ctx.converge(0.3, R_BOUNDARY)
        for i in range(len(trace.orbit) - 1):
            x_n = trace.orbit[i]
            x_next_expected = R_BOUNDARY * x_n * (1.0 - x_n)
            assert trace.orbit[i + 1] == pytest.approx(x_next_expected, rel=1e-12)


# ---------------------------------------------------------------------------
# SingularityContext.orbit_stream
# ---------------------------------------------------------------------------

class TestOrbitStream:
    def test_stream_yields_initial_value_first(self):
        ctx = SingularityContext()
        gen = ctx.orbit_stream(0.42, R_BOUNDARY)
        assert next(gen) == pytest.approx(0.42)

    def test_stream_second_value_follows_logistic_map(self):
        ctx = SingularityContext()
        gen = ctx.orbit_stream(0.4, R_BOUNDARY)
        x0 = next(gen)
        x1 = next(gen)
        assert x1 == pytest.approx(R_BOUNDARY * x0 * (1.0 - x0))

    def test_stream_converges_after_many_steps(self):
        ctx = SingularityContext()
        gen = ctx.orbit_stream(0.1, R_BOUNDARY)
        x = 0.0
        for _ in range(2000):
            x = next(gen)
        assert abs(x - INERT_CONSTANT) < 1e-6


# ---------------------------------------------------------------------------
# SingularityContext.prove_boundary
# ---------------------------------------------------------------------------

class TestProveBoundary:
    def test_returns_dict(self):
        ctx = SingularityContext()
        proof = ctx.prove_boundary()
        assert isinstance(proof, dict)

    def test_boundary_field(self):
        ctx = SingularityContext()
        proof = ctx.prove_boundary()
        assert proof["boundary"] == pytest.approx(R_BOUNDARY)

    def test_fixed_point_symbolic(self):
        ctx = SingularityContext()
        proof = ctx.prove_boundary()
        assert proof["fixed_point_symbolic"] == "7/12"

    def test_fixed_point_numerical_matches_7_over_12(self):
        ctx = SingularityContext()
        proof = ctx.prove_boundary()
        assert proof["fixed_point_numerical"] == pytest.approx(7 / 12, abs=1e-14)

    def test_numerical_match_flag(self):
        ctx = SingularityContext()
        proof = ctx.prove_boundary()
        assert proof["numerical_match"] is True

    def test_is_stable_flag(self):
        ctx = SingularityContext()
        proof = ctx.prove_boundary()
        assert proof["is_stable"] is True

    def test_banach_condition_holds(self):
        ctx = SingularityContext()
        proof = ctx.prove_boundary()
        assert proof["banach_condition_holds"] is True
        assert proof["contraction_constant_L"] < 1.0

    def test_all_test_points_converge(self):
        ctx = SingularityContext()
        proof = ctx.prove_boundary()
        assert proof["all_converge"] is True

    def test_convergence_from_each_test_point(self):
        ctx = SingularityContext()
        proof = ctx.prove_boundary()
        for x0, converged in proof["convergence_from_test_points"].items():
            assert converged is True, f"Did not converge from x0={x0}"

    def test_derivation_string_present(self):
        ctx = SingularityContext()
        proof = ctx.prove_boundary()
        assert "7/12" in proof["derivation"]
        assert "2.4" in proof["derivation"]


# ---------------------------------------------------------------------------
# recursive_contextualize — four-layer structure
# ---------------------------------------------------------------------------

class TestRecursiveContextualize:
    def test_returns_dict(self):
        result = recursive_contextualize()
        assert isinstance(result, dict)

    def test_layer_0_present(self):
        result = recursive_contextualize()
        assert "layer_0_map" in result
        assert "f(x)" in result["layer_0_map"]

    def test_layer_1_present(self):
        result = recursive_contextualize()
        assert "layer_1_boundary" in result
        assert "2.4" in result["layer_1_boundary"]

    def test_layer_2_contains_proof(self):
        result = recursive_contextualize()
        proof = result["layer_2_fixed_point"]
        assert proof["all_converge"] is True
        assert proof["banach_condition_holds"] is True

    def test_layer_3_self_reference(self):
        result = recursive_contextualize()
        sr = result["layer_3_self_reference"]
        assert sr["identity_holds"] is True

    def test_layer_3_f_x_star_equals_x_star(self):
        result = recursive_contextualize()
        sr = result["layer_3_self_reference"]
        assert sr["f(x_star)"] == pytest.approx(sr["x_star"], abs=1e-13)

    def test_layer_3_residual_below_threshold(self):
        result = recursive_contextualize()
        sr = result["layer_3_self_reference"]
        assert sr["residual"] < 1e-14

    def test_all_four_layers_present(self):
        result = recursive_contextualize()
        for key in ("layer_0_map", "layer_1_boundary",
                    "layer_2_fixed_point", "layer_3_self_reference"):
            assert key in result, f"Missing key: {key}"
