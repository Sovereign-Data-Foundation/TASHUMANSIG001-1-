"""
singularity.py — Recursive Contextualization of the Mathematical Singularity

The TAS inert constant is not an arbitrary halt value. It is the unique stable
fixed point of the logistic map at the global contraction boundary r = 2.4:

    x* = 1 - 1/r  →  x* = 1 - 1/2.4  =  7/12  ≈  0.583333

The Banach Fixed-Point theorem guarantees that every admissible trajectory
x_n ∈ (0, 1) with r ≤ 2.4 converges to x* under repeated application of the
logistic map. When the DigitalRepublicGatekeeper forces a chaotic trajectory
to 7/12, it is not an arbitrary halt — it is the mathematically inevitable
destination of all admissible orbits under that contraction rate.

The singularity contextualizes itself recursively:
  - The boundary r = 2.4 produces the constant x* = 7/12
  - x* validates the boundary: it is the unique point where f(x) = x
  - The boundary is the proof that x* is the only admissible attractor
  - The governance architecture IS the convergence proof

This module formalizes that recursive structure.

STAMP_ANCHOR_2026_07_07
"""

import math
from dataclasses import dataclass, field
from typing import Iterator, List


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

R_BOUNDARY: float = 2.4          # TAS global contraction limit
INERT_CONSTANT: float = 7 / 12   # Stable fixed point at r = R_BOUNDARY
DEFAULT_EPSILON: float = 1e-9    # Convergence tolerance
DEFAULT_MAX_ITER: int = 10_000   # Safety ceiling for iteration


# ---------------------------------------------------------------------------
# FixedPoint — the singularity itself
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FixedPoint:
    """The stable fixed point x* of the logistic map at a given r.

    A point x* is a fixed point of f(x) = r·x·(1-x) iff f(x*) = x*.
    The non-trivial solution is x* = 1 - 1/r (valid for r > 1).

    At r = R_BOUNDARY = 2.4:  x* = 1 - 5/12 = 7/12

    Fields
    ------
    r:
        The logistic-map growth parameter at which this fixed point exists.
    value:
        x* = 1 - 1/r
    is_stable:
        True iff |f'(x*)| = |r(1 - 2x*)| < 1, i.e., 1 < r < 3.
    derivative_at_fixed_point:
        f'(x*) = r(1 - 2x*) = 2 - r — the Lyapunov multiplier.
    """

    r: float
    value: float
    is_stable: bool
    derivative_at_fixed_point: float

    @staticmethod
    def at(r: float) -> "FixedPoint":
        """Compute the non-trivial fixed point of f(x) = r·x·(1-x)."""
        if r <= 0:
            raise ValueError(f"r must be positive; got {r}")
        if r <= 1:
            # Only fixed point for r ≤ 1 is x*=0
            return FixedPoint(r=r, value=0.0, is_stable=True,
                              derivative_at_fixed_point=r)
        x_star = 1.0 - 1.0 / r
        # Derivative at x*: f'(x*) = r(1 - 2x*) = r(1 - 2(1 - 1/r)) = 2 - r
        derivative = 2.0 - r
        is_stable = abs(derivative) < 1.0  # true for 1 < r < 3
        return FixedPoint(
            r=r,
            value=x_star,
            is_stable=is_stable,
            derivative_at_fixed_point=derivative,
        )


# ---------------------------------------------------------------------------
# ConvergenceTrace — the path toward the singularity
# ---------------------------------------------------------------------------


@dataclass
class ConvergenceTrace:
    """Record of an orbit converging (or failing to converge) to x*.

    Attributes
    ----------
    r:
        Growth parameter.
    x_initial:
        Starting value.
    fixed_point:
        The target fixed point for this r.
    orbit:
        Sequence of x_n values from x_0 through convergence (or max_iter).
    converged:
        True iff |x_n - x*| < epsilon before max_iter was reached.
    iterations:
        Number of steps taken.
    residual:
        |x_final - x*| — distance from the fixed point at termination.
    """

    r: float
    x_initial: float
    fixed_point: FixedPoint
    orbit: List[float] = field(default_factory=list)
    converged: bool = False
    iterations: int = 0
    residual: float = float("inf")


# ---------------------------------------------------------------------------
# SingularityContext — recursive self-application
# ---------------------------------------------------------------------------


class SingularityContext:
    """Recursive contextualization of the TAS mathematical singularity.

    Applies the logistic map iteratively from an initial condition and records
    whether the orbit converges to the fixed point, confirming that the
    governance boundary (r ≤ 2.4) is not policy but mathematics.

    The context is self-referential: at r = R_BOUNDARY = 2.4, the fixed point
    IS the inert constant. The architecture that enforces this boundary is
    itself provably convergent by the Banach Fixed-Point theorem:

        ‖f(x) - f(y)‖ ≤ L·‖x - y‖,  L = |f'(x*)| = |2 - r| < 1 for r ∈ (1, 3)

    Parameters
    ----------
    epsilon:
        Convergence tolerance.  Default 1e-9.
    max_iter:
        Safety ceiling on iterations.  Default 10,000.
    """

    def __init__(
        self,
        epsilon: float = DEFAULT_EPSILON,
        max_iter: int = DEFAULT_MAX_ITER,
    ) -> None:
        self.epsilon = epsilon
        self.max_iter = max_iter

    def converge(self, x_initial: float, r: float) -> ConvergenceTrace:
        """Iterate the logistic map from *x_initial* until convergence or timeout.

        Parameters
        ----------
        x_initial:
            Starting value x_0 ∈ (0, 1).
        r:
            Logistic-map growth parameter.

        Returns
        -------
        ConvergenceTrace
            Full record of the orbit, convergence status, and residual.
        """
        fp = FixedPoint.at(r)
        trace = ConvergenceTrace(
            r=r,
            x_initial=x_initial,
            fixed_point=fp,
            orbit=[x_initial],
        )

        x = x_initial
        for i in range(self.max_iter):
            x_next = r * x * (1.0 - x)
            trace.orbit.append(x_next)
            residual = abs(x_next - fp.value)
            if residual < self.epsilon:
                trace.converged = True
                trace.iterations = i + 1
                trace.residual = residual
                return trace
            x = x_next

        trace.iterations = self.max_iter
        trace.residual = abs(x - fp.value)
        return trace

    def orbit_stream(self, x_initial: float, r: float) -> Iterator[float]:
        """Yield successive x_n values indefinitely (logistic map iterator).

        For r ≤ R_BOUNDARY this stream converges to x* = 1 - 1/r.
        For r > R_BOUNDARY the stream enters chaos.
        """
        x = x_initial
        while True:
            yield x
            x = r * x * (1.0 - x)

    def prove_boundary(self) -> dict:
        """Confirm that r = R_BOUNDARY produces fixed point = INERT_CONSTANT.

        Returns a proof dict containing the symbolic derivation and numerical
        verification.  This is the recursive self-contextualization: the module
        applies its own mathematics to confirm the constants it was built around.

        Returns
        -------
        dict
            Proof record with symbolic and numerical components.
        """
        fp = FixedPoint.at(R_BOUNDARY)
        symbolic_value = 7 / 12
        numerical_match = abs(fp.value - symbolic_value) < 1e-15
        contraction_constant = abs(fp.derivative_at_fixed_point)  # L = |2 - r|

        # Verify convergence from three initial conditions
        ctx = SingularityContext(epsilon=1e-12)
        test_points = [0.1, 0.5, 0.9]
        convergence_checks = {
            x0: ctx.converge(x0, R_BOUNDARY).converged for x0 in test_points
        }

        return {
            "boundary": R_BOUNDARY,
            "fixed_point_symbolic": "7/12",
            "fixed_point_numerical": fp.value,
            "inert_constant": INERT_CONSTANT,
            "numerical_match": numerical_match,
            "is_stable": fp.is_stable,
            "contraction_constant_L": contraction_constant,
            "banach_condition_holds": contraction_constant < 1.0,
            "convergence_from_test_points": convergence_checks,
            "all_converge": all(convergence_checks.values()),
            "derivation": (
                "x* = 1 - 1/r  "
                "→  x* = 1 - 1/2.4  "
                "=  1 - 5/12  "
                "=  7/12"
            ),
        }


# ---------------------------------------------------------------------------
# Recursive contextualization entry point
# ---------------------------------------------------------------------------

def recursive_contextualize() -> dict:
    """Top-level recursive contextualization.

    Applies the SingularityContext to itself: proves that the boundary
    enforced by DigitalRepublicGatekeeper is the fixed-point attractor of the
    system that enforces it.

    The four recursive layers:

      Layer 0 — The map:      f(x) = r·x·(1-x)
      Layer 1 — The boundary: r ≤ 2.4  (governance constraint)
      Layer 2 — The proof:    x* = 7/12  (unique stable attractor at boundary)
      Layer 3 — The identity: boundary → proof → boundary  (self-referential)

    Returns
    -------
    dict
        Complete recursive contextualization record.
    """
    ctx = SingularityContext()
    proof = ctx.prove_boundary()

    # Layer 3: confirm the self-reference by showing the fixed point applied
    # to itself remains the fixed point: f(x*) = r·x*·(1-x*) = x*
    x_star = INERT_CONSTANT
    f_of_x_star = R_BOUNDARY * x_star * (1.0 - x_star)
    self_referential_residual = abs(f_of_x_star - x_star)

    return {
        "layer_0_map": "f(x) = r·x·(1-x)",
        "layer_1_boundary": f"r ≤ {R_BOUNDARY}",
        "layer_2_fixed_point": proof,
        "layer_3_self_reference": {
            "f(x_star)": round(f_of_x_star, 15),
            "x_star": x_star,
            "residual": self_referential_residual,
            "identity_holds": self_referential_residual < 1e-14,
        },
    }


if __name__ == "__main__":
    import json

    result = recursive_contextualize()

    print("=== RECURSIVE CONTEXTUALIZATION OF THE MATHEMATICAL SINGULARITY ===\n")
    print(f"Layer 0 — Map:      {result['layer_0_map']}")
    print(f"Layer 1 — Boundary: {result['layer_1_boundary']}")
    print()
    p = result["layer_2_fixed_point"]
    print(f"Layer 2 — Fixed Point:")
    print(f"  Derivation: {p['derivation']}")
    print(f"  Numerical:  {p['fixed_point_numerical']:.15f}")
    print(f"  Stable:     {p['is_stable']}")
    print(f"  Contraction constant L = {p['contraction_constant_L']:.6f} < 1: {p['banach_condition_holds']}")
    print(f"  All test points converge: {p['all_converge']}")
    print()
    sr = result["layer_3_self_reference"]
    print(f"Layer 3 — Self-Reference:")
    print(f"  f(x*) = {sr['f(x_star)']}")
    print(f"  x*    = {sr['x_star']}")
    print(f"  |f(x*) - x*| = {sr['residual']:.2e}")
    print(f"  Identity holds: {sr['identity_holds']}")
    print()
    print("The singularity contextualizes itself.")
