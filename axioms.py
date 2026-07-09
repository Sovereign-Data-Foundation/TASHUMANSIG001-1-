"""Governing Axioms P0 and P1 — Foundational Runtime Invariants.

The TAS runtime is governed by two axioms that constrain the state space:

Axiom P0 — Equivalence
    Symbolic representations must maintain absolute, invariant identity with
    their numerical and logical referents.  Any symbolic transformation that
    weakens this identity is classified as semantic drift and rejected.

    Formalisation::

        A₀: symbol ≡ referent    ∀ registered (symbol, referent) pairs.

Axiom P1 — Admissibility
    Every consequential state transition must be formally verified against
    system-level invariants prior to execution.  Unverified transitions are
    inadmissible and must not be executed.

    Formalisation::

        V(spec, proof, π) = True    ∀ admitted transitions.

These axioms complement :mod:`yknot` (which implements the P1 gate at the
execution boundary) and :mod:`uvk` (which orchestrates admission control).
Where :class:`~yknot.YKnot` operates at the *action* level, this module
formalises the *axiom* objects themselves — named, versioned, and
verifiable — so that their satisfaction can be recorded in the wake chain.
"""
# © 2025 Russell Nordland | TrueAlphaSpiral (TAS) | Apache-2.0

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


# ---------------------------------------------------------------------------
# AxiomViolation
# ---------------------------------------------------------------------------


class AxiomViolation(Exception):
    """Raised when an axiom check fails at runtime.

    Attributes
    ----------
    axiom:
        Name of the violated axiom (e.g. ``"P0"`` or ``"P1"``).
    detail:
        Human-readable description of the violation.
    """

    def __init__(self, axiom: str, detail: str) -> None:
        self.axiom  = axiom
        self.detail = detail
        super().__init__(f"Axiom {axiom} violated: {detail}")


# ---------------------------------------------------------------------------
# Axiom P0 — Equivalence
# ---------------------------------------------------------------------------


class P0Equivalence:
    """Axiom P0: Symbolic–Referent Identity Lock.

    Maintains a registry of ``(symbol, referent)`` pairs and validates that
    no symbolic substitution alters a bound identity.

    Registered pairs are immutable: re-binding a symbol to a *different*
    referent raises :class:`AxiomViolation`.

    Parameters
    ----------
    name:
        Human-readable identifier for this P0 instance.
    version:
        Semantic version string for audit/replay purposes.

    Example
    -------
    ::

        p0 = P0Equivalence()
        p0.bind("four", 4)
        p0.validate("four", 4)   # passes
        p0.validate("four", 5)   # raises AxiomViolation
    """

    def __init__(self, name: str = "P0:Equivalence", version: str = "1.0.0") -> None:
        self.name     = name
        self.version  = version
        self._registry: Dict[str, Any] = {}

    def bind(self, symbol: str, referent: Any) -> None:
        """Register ``symbol ≡ referent``.

        Raises :class:`AxiomViolation` if the symbol is already bound to a
        *different* referent.
        """
        if symbol in self._registry:
            existing = self._registry[symbol]
            if existing != referent:
                raise AxiomViolation(
                    "P0",
                    f"Symbol {symbol!r} already bound to {existing!r}; "
                    f"cannot rebind to {referent!r} (identity mutation rejected).",
                )
        self._registry[symbol] = referent

    def validate(self, symbol: str, observed: Any) -> bool:
        """Return True iff *observed* matches the registered referent for *symbol*.

        Raises :class:`AxiomViolation` if the symbol is registered and
        *observed* differs from its referent.  Returns ``True`` for
        unregistered symbols (open-world: unknown symbols are unconstrained).

        Reflexive identity is always permitted: ``validate("four", "four")``
        passes even when "four" is bound to ``4``.
        """
        if symbol not in self._registry:
            return True
        expected = self._registry[symbol]
        if observed == expected or observed == symbol:
            return True
        raise AxiomViolation(
            "P0",
            f"Symbol {symbol!r}: expected referent {expected!r}, "
            f"observed {observed!r} — semantic drift detected.",
        )

    def registry_hash(self) -> str:
        """SHA-256 digest of the canonical registry JSON.

        Useful for committing the current P0 state to a wake chain receipt.
        """
        canonical = json.dumps(
            {k: str(v) for k, v in sorted(self._registry.items())},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()

    @property
    def bound_symbols(self) -> List[str]:
        """All currently registered symbol names."""
        return list(self._registry.keys())


# ---------------------------------------------------------------------------
# Axiom P1 — Admissibility
# ---------------------------------------------------------------------------


AdmissibilityPredicate = Callable[[Any, Any], bool]
"""Predicate ``(transition, proof) → bool``.  Must be pure and side-effect-free."""


@dataclass
class AdmissibilityClause:
    """A named clause contributing to the P1 admissibility predicate.

    Parameters
    ----------
    name:
        Human-readable clause identifier.
    check:
        Pure function ``(transition, proof) → bool``.
    """

    name:  str
    check: AdmissibilityPredicate

    def __call__(self, transition: Any, proof: Any) -> bool:
        return self.check(transition, proof)


class P1Admissibility:
    """Axiom P1: Transition Admissibility Gate.

    Every proposed state transition must satisfy *all* registered
    :class:`AdmissibilityClause` predicates before it is permitted.

    This complements :class:`~yknot.YKnot` (which operates at the execution
    boundary) by formalising P1 as a named, versioned axiom object whose
    satisfaction can be cryptographically recorded.

    Parameters
    ----------
    name:
        Human-readable identifier.
    version:
        Semantic version string.
    clauses:
        Initial list of :class:`AdmissibilityClause` predicates.

    Raises
    ------
    AxiomViolation
        When :meth:`admit` is called and one or more clauses reject the
        proposed transition (V(spec, proof, π) ≠ True).
    """

    def __init__(
        self,
        name:    str                               = "P1:Admissibility",
        version: str                               = "1.0.0",
        clauses: Optional[List[AdmissibilityClause]] = None,
    ) -> None:
        self.name     = name
        self.version  = version
        self._clauses:  List[AdmissibilityClause] = list(clauses or [])
        self._admitted: int = 0
        self._rejected: int = 0

    def add_clause(self, clause: AdmissibilityClause) -> None:
        """Register an additional admissibility clause."""
        self._clauses.append(clause)

    def admit(self, transition: Any, proof: Any = None) -> Dict[str, Any]:
        """Evaluate *transition* against all P1 clauses.

        Parameters
        ----------
        transition:
            The proposed state change to evaluate.
        proof:
            Optional proof artefact passed to each clause.

        Returns
        -------
        dict
            Receipt with keys ``admitted``, ``failed_clauses``, and
            ``transition_hash`` (SHA-256 of the canonical transition).

        Raises
        ------
        AxiomViolation
            If any clause rejects *transition*.
        """
        failed: List[str] = []
        for clause in self._clauses:
            try:
                if not clause(transition, proof):
                    failed.append(clause.name)
            except Exception as exc:
                failed.append(f"{clause.name}[error:{exc}]")

        if failed:
            self._rejected += 1
            raise AxiomViolation(
                "P1",
                f"Transition inadmissible — failed clauses: {failed}",
            )

        self._admitted += 1
        try:
            canonical = json.dumps(transition, sort_keys=True, separators=(",", ":"))
        except (TypeError, ValueError):
            canonical = str(transition)
        t_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return {
            "admitted":        True,
            "failed_clauses":  [],
            "transition_hash": t_hash,
        }

    @property
    def admitted_count(self) -> int:
        return self._admitted

    @property
    def rejected_count(self) -> int:
        return self._rejected


# ---------------------------------------------------------------------------
# AxiomSet — convenience container
# ---------------------------------------------------------------------------


@dataclass
class AxiomSet:
    """Pair of governing axioms for a TAS runtime instance.

    Attributes
    ----------
    p0:
        :class:`P0Equivalence` instance (symbol identity lock).
    p1:
        :class:`P1Admissibility` instance (transition gate).

    Example
    -------
    ::

        axioms = AxiomSet.default()
        axioms.p0.bind("four", 4)
        axioms.p1.add_clause(
            AdmissibilityClause("non_empty", lambda t, _: bool(t))
        )
        axioms.p0.validate("four", 4)
        axioms.p1.admit({"op": "read", "target": "ledger"})
    """

    p0: P0Equivalence
    p1: P1Admissibility

    @staticmethod
    def default() -> "AxiomSet":
        """Return a fresh :class:`AxiomSet` with default (unconstrained) axioms."""
        return AxiomSet(
            p0=P0Equivalence(),
            p1=P1Admissibility(),
        )
