"""Problem Statement Versioning Protocol (PSVP).

Translates natural-language proposals into deterministic, cryptographically
anchored :class:`SpecArtifact` objects before any execution is permitted.

Pipeline
--------
1. **Decompose** — Split proposal text into typed :class:`Claim` nodes.  Each
   node is assigned a SHA-256 content hash and a Shannon entropy energy score.
2. **Spec Gate** — Evaluate the :class:`ClaimGraph` density.  Proposals whose
   mean entropy falls below ``min_density`` are rejected as information-poor
   ("ambiguous").  When a prior graph exists, the entropy change rate
   ``|ΔH / Δt|`` is also checked against ``drift_ceiling``.
3. **Version** — Emit a :class:`SpecArtifact`: a versioned, self-describing
   envelope whose ``spec_id`` SHA-256 chains it to any predecessor spec.

Shannon Entropy (H)
-------------------
::

    H = -Σ pᵢ · log₂(pᵢ)

where ``pᵢ`` is the relative token frequency in the claim text.

Drift Gate
----------
::

    |ΔH / Δt| > drift_ceiling  →  reject  (ambiguity spike)
    |ΔH / Δt| ≤ drift_ceiling  →  pass
"""
# © 2025 Russell Nordland | TrueAlphaSpiral (TAS) | Apache-2.0

from __future__ import annotations

import hashlib
import json
import math
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _tokenise(text: str) -> List[str]:
    stripped = text.lower()
    for ch in ".,;:!?\"'()[]{}":
        stripped = stripped.replace(ch, " ")
    return [t for t in stripped.split() if t]


def shannon_entropy(tokens: Sequence[str]) -> float:
    """Return H = -Σ pᵢ·log₂(pᵢ) for the token sequence.

    Returns 0.0 for an empty sequence.
    """
    if not tokens:
        return 0.0
    counts: Dict[str, int] = {}
    for t in tokens:
        counts[t] = counts.get(t, 0) + 1
    total = len(tokens)
    h = 0.0
    for c in counts.values():
        p = c / total
        h -= p * math.log2(p)
    return h


# ---------------------------------------------------------------------------
# Claim
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Claim:
    """A single verifiable proposition extracted from a proposal.

    Attributes
    ----------
    index:
        Zero-based position in the parent :class:`ClaimGraph`.
    text:
        Original claim text.
    sha256:
        SHA-256 hex digest of the UTF-8 encoded *text*.
    entropy:
        Shannon entropy of the tokenised *text*.
    """

    index:   int
    text:    str
    sha256:  str
    entropy: float

    @staticmethod
    def from_text(index: int, text: str) -> "Claim":
        tokens = _tokenise(text)
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return Claim(index=index, text=text, sha256=digest,
                     entropy=shannon_entropy(tokens))

    def to_dict(self) -> Dict:
        return {
            "index":   self.index,
            "text":    self.text,
            "sha256":  self.sha256,
            "entropy": self.entropy,
        }


# ---------------------------------------------------------------------------
# ClaimGraph
# ---------------------------------------------------------------------------


@dataclass
class ClaimGraph:
    """A directed dependency graph of :class:`Claim` nodes.

    Attributes
    ----------
    claims:
        Ordered list of claims decomposed from the source proposal.
    dependencies:
        Mapping ``{claim_index: [dependency_indices]}``.  An empty mapping
        implies no explicit dependencies have been declared.
    timestamp:
        Unix epoch at which the graph was constructed.
    """

    claims:       List[Claim]
    dependencies: Dict[int, List[int]] = field(default_factory=dict)
    timestamp:    float                 = field(default_factory=time.time)

    @property
    def mean_entropy(self) -> float:
        """Mean Shannon entropy across all claims.  0.0 if no claims."""
        if not self.claims:
            return 0.0
        return sum(c.entropy for c in self.claims) / len(self.claims)

    @property
    def graph_hash(self) -> str:
        """SHA-256 digest of the concatenated claim-hash chain."""
        concatenated = "".join(c.sha256 for c in self.claims)
        return hashlib.sha256(concatenated.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict:
        return {
            "claims":       [c.to_dict() for c in self.claims],
            "dependencies": {str(k): v for k, v in self.dependencies.items()},
            "timestamp":    self.timestamp,
            "mean_entropy": self.mean_entropy,
            "graph_hash":   self.graph_hash,
        }


# ---------------------------------------------------------------------------
# SpecArtifact
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SpecArtifact:
    """Versioned, cryptographically anchored specification artifact.

    Attributes
    ----------
    spec_id:
        SHA-256 hex digest of the canonical spec payload.
    version:
        Monotone integer counter (1-indexed within a :class:`PSVP` instance).
    graph_hash:
        :attr:`ClaimGraph.graph_hash` of the source graph (initial energy E₀).
    mean_entropy:
        Mean claim entropy (E₀).
    predecessor_id:
        ``spec_id`` of the immediately preceding artifact, or ``None`` for the
        genesis spec.
    timestamp:
        Unix epoch at which this artifact was emitted.
    """

    spec_id:        str
    version:        int
    graph_hash:     str
    mean_entropy:   float
    predecessor_id: Optional[str]
    timestamp:      float

    def to_dict(self) -> Dict:
        return {
            "spec_id":        self.spec_id,
            "version":        self.version,
            "graph_hash":     self.graph_hash,
            "mean_entropy":   self.mean_entropy,
            "predecessor_id": self.predecessor_id,
            "timestamp":      self.timestamp,
        }


def _compute_spec_id(
    version:        int,
    graph_hash:     str,
    mean_entropy:   float,
    predecessor_id: Optional[str],
    timestamp:      float,
) -> str:
    payload = json.dumps(
        {
            "version":        version,
            "graph_hash":     graph_hash,
            "mean_entropy":   mean_entropy,
            "predecessor_id": predecessor_id,
            "timestamp":      timestamp,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


# ---------------------------------------------------------------------------
# DriftGateError
# ---------------------------------------------------------------------------


class DriftGateError(Exception):
    """Raised when a proposal fails the PSVP density or drift gate.

    Attributes
    ----------
    reason:
        ``"low_density"`` or ``"drift_spike"``.
    entropy:
        Observed entropy value that triggered the gate.
    threshold:
        The gate threshold that was violated.
    """

    def __init__(self, reason: str, entropy: float, threshold: float) -> None:
        self.reason    = reason
        self.entropy   = entropy
        self.threshold = threshold
        super().__init__(
            f"PSVP drift gate rejected: "
            f"reason={reason!r}  entropy={entropy:.4f}  threshold={threshold:.4f}"
        )


# ---------------------------------------------------------------------------
# PSVP
# ---------------------------------------------------------------------------


class PSVP:
    """Problem Statement Versioning Protocol engine.

    Parameters
    ----------
    min_density:
        Minimum mean claim entropy required to pass the density gate.
    drift_ceiling:
        Maximum ``|ΔH / Δt|`` permitted between consecutive specs.
        ``None`` disables the drift-rate check.
    sentence_delimiters:
        Characters used to split the raw proposal into individual claims.
    """

    def __init__(
        self,
        min_density:         float          = 0.5,
        drift_ceiling:       Optional[float] = 2.0,
        sentence_delimiters: str            = ".!?;",
    ) -> None:
        self.min_density         = min_density
        self.drift_ceiling       = drift_ceiling
        self.sentence_delimiters = sentence_delimiters

        self._version:        int                = 0
        self._last_entropy:   Optional[float]    = None
        self._last_timestamp: Optional[float]    = None
        self._last_spec_id:   Optional[str]      = None
        self._history:        List[SpecArtifact] = []

    # ------------------------------------------------------------------
    # Decompose
    # ------------------------------------------------------------------

    def decompose(self, proposal: str) -> ClaimGraph:
        """Split *proposal* into a :class:`ClaimGraph`.

        Each sentence (delimited by :attr:`sentence_delimiters`) becomes one
        :class:`Claim`.  A linear dependency chain links consecutive claims.
        """
        raw: List[str] = [proposal]
        for delim in self.sentence_delimiters:
            expanded: List[str] = []
            for s in raw:
                for part in s.split(delim):
                    cleaned = part.strip()
                    if cleaned:
                        expanded.append(cleaned)
            raw = expanded

        claims = [Claim.from_text(i, s) for i, s in enumerate(raw)]
        deps: Dict[int, List[int]] = {i: [i - 1] for i in range(1, len(claims))}
        return ClaimGraph(claims=claims, dependencies=deps)

    # ------------------------------------------------------------------
    # Gate helpers
    # ------------------------------------------------------------------

    def _check_density(self, graph: ClaimGraph) -> None:
        h = graph.mean_entropy
        if h < self.min_density:
            raise DriftGateError("low_density", h, self.min_density)

    def _check_drift(self, graph: ClaimGraph, now: float) -> None:
        if self.drift_ceiling is None:
            return
        if self._last_entropy is None or self._last_timestamp is None:
            return
        dt = now - self._last_timestamp
        if dt <= 0:
            return
        dh_dt = abs(graph.mean_entropy - self._last_entropy) / dt
        if dh_dt > self.drift_ceiling:
            raise DriftGateError("drift_spike", dh_dt, self.drift_ceiling)

    # ------------------------------------------------------------------
    # Spec creation
    # ------------------------------------------------------------------

    def create_spec(
        self,
        graph:     ClaimGraph,
        timestamp: Optional[float] = None,
    ) -> SpecArtifact:
        """Validate *graph* against both gates and emit a :class:`SpecArtifact`.

        Raises :class:`DriftGateError` if the proposal is rejected.
        Inject *timestamp* in tests for temporal immutability.
        """
        now = timestamp if timestamp is not None else time.time()

        self._check_density(graph)
        self._check_drift(graph, now)

        self._version += 1
        spec_id = _compute_spec_id(
            version        = self._version,
            graph_hash     = graph.graph_hash,
            mean_entropy   = graph.mean_entropy,
            predecessor_id = self._last_spec_id,
            timestamp      = now,
        )
        artifact = SpecArtifact(
            spec_id        = spec_id,
            version        = self._version,
            graph_hash     = graph.graph_hash,
            mean_entropy   = graph.mean_entropy,
            predecessor_id = self._last_spec_id,
            timestamp      = now,
        )
        self._last_entropy   = graph.mean_entropy
        self._last_timestamp = now
        self._last_spec_id   = spec_id
        self._history.append(artifact)
        return artifact

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    @property
    def history(self) -> List[SpecArtifact]:
        """All emitted :class:`SpecArtifact` instances (oldest first)."""
        return list(self._history)

    @property
    def version(self) -> int:
        """Current spec version counter."""
        return self._version
