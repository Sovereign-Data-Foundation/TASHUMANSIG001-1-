"""Truth Audit Engine — Decision-Strain Monitoring.

Evaluates every consequential state transition across five dimensions,
computing a composite "decision-strain" score that quantifies how far
execution has drifted from ground-truth coherence.

Dimensions
----------
FACTUAL       — correspondence to verifiable, external facts.
LOGICAL       — internal consistency and deductive validity.
ETHICAL       — alignment with declared ethical constraints.
BIAS          — systematic skew away from neutral representation.
HALLUCINATION — presence of unsupported or fabricated claims.

Decision-Strain (DS)
--------------------
::

    DS = 1 - (Σ wᵢ · scoreᵢ) / (Σ wᵢ)

where ``scoreᵢ ∈ [0, 1]`` is the compliance score for dimension ``i``
(1.0 = fully compliant) and ``wᵢ`` is the dimension weight.

DS = 0.0  →  perfect alignment.
DS = 1.0  →  complete collapse.

When :attr:`TruthAuditEngine.strain_ceiling` is set and exceeded, a
:class:`StrainCeilingBreached` exception is raised so the caller can
invoke the Phoenix recovery protocol.
"""
# © 2025 Russell Nordland | TrueAlphaSpiral (TAS) | Apache-2.0

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Sequence


# ---------------------------------------------------------------------------
# Audit Dimensions
# ---------------------------------------------------------------------------


class AuditDimension(Enum):
    """The five dimensions of decision-strain evaluation."""

    FACTUAL       = auto()
    LOGICAL       = auto()
    ETHICAL       = auto()
    BIAS          = auto()
    HALLUCINATION = auto()


DEFAULT_WEIGHTS: Dict[AuditDimension, float] = {
    AuditDimension.FACTUAL:       1.0,
    AuditDimension.LOGICAL:       1.0,
    AuditDimension.ETHICAL:       1.0,
    AuditDimension.BIAS:          1.0,
    AuditDimension.HALLUCINATION: 1.0,
}


# ---------------------------------------------------------------------------
# DimensionScore
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DimensionScore:
    """Compliance score for a single audit dimension.

    Attributes
    ----------
    dimension:
        The :class:`AuditDimension` being evaluated.
    score:
        Compliance score in ``[0.0, 1.0]``.  1.0 = fully compliant.
    evidence:
        Human-readable rationale or supporting evidence.
    """

    dimension: AuditDimension
    score:     float
    evidence:  str = ""

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(
                f"DimensionScore.score must be in [0, 1]; got {self.score!r}"
            )


# ---------------------------------------------------------------------------
# DecisionStrain
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DecisionStrain:
    """Composite audit result across all five dimensions.

    Attributes
    ----------
    scores:
        Per-dimension :class:`DimensionScore` list.
    strain:
        Weighted decision-strain DS ∈ [0.0, 1.0].
    timestamp:
        Unix epoch at which the audit was performed.
    action:
        Optional identifier for the action being audited.
    """

    scores:    List[DimensionScore]
    strain:    float
    timestamp: float
    action:    str = ""

    def score_for(self, dimension: AuditDimension) -> Optional[float]:
        """Return the compliance score for *dimension*, or ``None``."""
        for s in self.scores:
            if s.dimension == dimension:
                return s.score
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action":    self.action,
            "strain":    self.strain,
            "timestamp": self.timestamp,
            "scores": [
                {
                    "dimension": s.dimension.name,
                    "score":     s.score,
                    "evidence":  s.evidence,
                }
                for s in self.scores
            ],
        }


# ---------------------------------------------------------------------------
# StrainCeilingBreached
# ---------------------------------------------------------------------------


class StrainCeilingBreached(Exception):
    """Raised when composite decision-strain exceeds the configured ceiling.

    Attributes
    ----------
    strain:
        The observed composite strain.
    ceiling:
        The threshold that was exceeded.
    audit:
        The full :class:`DecisionStrain` record that triggered the breach.
    """

    def __init__(self, strain: float, ceiling: float, audit: DecisionStrain) -> None:
        self.strain  = strain
        self.ceiling = ceiling
        self.audit   = audit
        super().__init__(
            f"Decision-strain ceiling breached: "
            f"DS={strain:.4f}  ceiling={ceiling:.4f}  action={audit.action!r}"
        )


# ---------------------------------------------------------------------------
# TruthAuditEngine
# ---------------------------------------------------------------------------


class TruthAuditEngine:
    """Evaluate state transitions for decision-strain across five dimensions.

    Parameters
    ----------
    weights:
        Per-dimension weight mapping.  Defaults to :data:`DEFAULT_WEIGHTS`
        (equal weighting).
    strain_ceiling:
        DS threshold above which :class:`StrainCeilingBreached` is raised.
        ``None`` disables the auto-raise.
    scorers:
        Optional mapping ``{AuditDimension: callable(action, context) → float}``.
        When provided, :meth:`evaluate` invokes these for any dimension not
        covered by caller-supplied scores.
    """

    def __init__(
        self,
        weights:        Optional[Dict[AuditDimension, float]] = None,
        strain_ceiling: Optional[float]                       = None,
        scorers:        Optional[Dict[AuditDimension, Callable]] = None,
    ) -> None:
        self._weights:       Dict[AuditDimension, float]    = dict(weights or DEFAULT_WEIGHTS)
        self.strain_ceiling: Optional[float]                = strain_ceiling
        self._scorers:       Dict[AuditDimension, Callable] = dict(scorers or {})
        self._history:       List[DecisionStrain]           = []

    # ------------------------------------------------------------------
    # Strain computation
    # ------------------------------------------------------------------

    def compute_strain(self, scores: Sequence[DimensionScore]) -> float:
        """Compute weighted DS = 1 - (Σ wᵢ·scoreᵢ) / (Σ wᵢ).

        Dimensions absent from *scores* are treated as score=0.0
        (worst-case assumption: absence of evidence = non-compliance).
        """
        score_map = {s.dimension: s.score for s in scores}
        total_w  = 0.0
        weighted = 0.0
        for dim, w in self._weights.items():
            if w == 0.0:
                continue
            total_w  += w
            weighted += w * score_map.get(dim, 0.0)
        if total_w == 0.0:
            return 0.0
        return 1.0 - weighted / total_w

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def evaluate(
        self,
        action:    str,
        context:   Any                         = None,
        scores:    Optional[List[DimensionScore]] = None,
        timestamp: Optional[float]             = None,
    ) -> DecisionStrain:
        """Audit *action* and return a :class:`DecisionStrain`.

        Parameters
        ----------
        action:
            Identifier or description of the state transition being audited.
        context:
            Arbitrary context passed to registered scorer callables.
        scores:
            Pre-computed :class:`DimensionScore` list.  Registered scorers
            fill in any uncovered dimensions.
        timestamp:
            Override timestamp (inject a fixed value in tests).

        Raises
        ------
        StrainCeilingBreached
            If the composite strain exceeds :attr:`strain_ceiling`.
        """
        now = timestamp if timestamp is not None else time.time()

        score_map: Dict[AuditDimension, DimensionScore] = {}
        for s in (scores or []):
            score_map[s.dimension] = s

        for dim, scorer_fn in self._scorers.items():
            if dim not in score_map:
                raw = scorer_fn(action, context)
                score_map[dim] = DimensionScore(dimension=dim, score=float(raw))

        final_scores = list(score_map.values())
        strain       = self.compute_strain(final_scores)

        audit = DecisionStrain(
            scores    = final_scores,
            strain    = strain,
            timestamp = now,
            action    = action,
        )
        self._history.append(audit)

        if self.strain_ceiling is not None and strain > self.strain_ceiling:
            raise StrainCeilingBreached(strain, self.strain_ceiling, audit)

        return audit

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    @property
    def history(self) -> List[DecisionStrain]:
        """All :class:`DecisionStrain` records (oldest first)."""
        return list(self._history)

    @property
    def latest(self) -> Optional[DecisionStrain]:
        """Most recent :class:`DecisionStrain`, or ``None``."""
        return self._history[-1] if self._history else None

    def mean_strain(self) -> float:
        """Mean decision-strain across all audited actions.  0.0 if no history."""
        if not self._history:
            return 0.0
        return sum(a.strain for a in self._history) / len(self._history)
