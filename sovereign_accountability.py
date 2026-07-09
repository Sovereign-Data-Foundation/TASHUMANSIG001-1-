"""Sovereign Accountability — Structural Checks on Institutional Authority.

Grounded in John Adams' architectural principle that stable liberty requires
a government of *laws*, not of *men*:

    "A Constitution of Government once changed from Freedom, can never
     be restored."  — John Adams

Adams identified three structural threats to republican governance:

1. **Unchecked factions** — wealth, commercial monopolies, or any concentrated
   interest that places itself above the law.
2. **Single-branch dominance** — any arm of government capturing the functions
   of the others, collapsing the separation of powers.
3. **Subordination failure** — corporations and chartered entities acting as if
   they possessed sovereign immunity rather than deriving authority from the
   consent of the governed.

This module operationalises these concerns as runtime-checkable invariants
within the TAS capability framework:

* :class:`Branch`                  — enumerated governmental branches.
* :class:`SovereigntyTier`         — STATE and NATIONAL authority levels.
* :class:`BranchScope`             — bounded authority for a single branch.
* :class:`DualSovereignty`         — two-tier authority model with double security.
* :class:`FactionSubordination`    — enforces that no entity claims immunity.
* :class:`SovereignAccountability` — orchestrator with UVK invariant factory.

The Maxim of Accountability
---------------------------
    No corporate, institutional, or algorithmic interest is immune to the
    natural law of the land.  Authority is structurally inherited, not
    behaviourally asserted.
"""
# © 2025 Russell Nordland | TrueAlphaSpiral (TAS) | Apache-2.0

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set

from uvk import Invariant


# ---------------------------------------------------------------------------
# Branch
# ---------------------------------------------------------------------------


class Branch(Enum):
    """The three constitutionally separated branches of governance.

    Maps to distinct capability scopes that must not overlap without explicit
    inter-branch delegation.
    """

    EXECUTIVE   = auto()  # enforcement and administration
    JUDICIAL    = auto()  # interpretation and adjudication
    LEGISLATIVE = auto()  # rule-making and charter authority


# ---------------------------------------------------------------------------
# SovereigntyTier
# ---------------------------------------------------------------------------


class SovereigntyTier(Enum):
    """Dual-sovereignty tiers corresponding to Adams' federal model.

    STATE    — reserved powers; local scope.
    NATIONAL — delegated powers; system-wide scope.
    """

    STATE    = auto()
    NATIONAL = auto()


# ---------------------------------------------------------------------------
# SubordinationError
# ---------------------------------------------------------------------------


class SubordinationError(Exception):
    """Raised when a scope or entity attempts to claim sovereign immunity.

    Attributes
    ----------
    entity:
        Identifier of the entity that violated subordination.
    detail:
        Human-readable description of the violation.
    """

    def __init__(self, entity: str, detail: str) -> None:
        self.entity = entity
        self.detail = detail
        super().__init__(f"Subordination violation — {entity!r}: {detail}")


# ---------------------------------------------------------------------------
# BranchScope
# ---------------------------------------------------------------------------


@dataclass
class BranchScope:
    """Bounded authority envelope for a single :class:`Branch`.

    Each branch operates within a declared set of *permitted actions*.
    Any action outside this set is inadmissible (separation-of-powers
    enforcement).

    Parameters
    ----------
    branch:
        The governmental branch this scope represents.
    tier:
        Sovereignty tier (:attr:`SovereigntyTier.STATE` or
        :attr:`SovereigntyTier.NATIONAL`).
    permitted_actions:
        Set of action identifiers this branch is authorised to perform.
    immune:
        If ``True`` this scope claims sovereign immunity — always rejected by
        :class:`FactionSubordination` and :class:`DualSovereignty`.
    """

    branch:            Branch
    tier:              SovereigntyTier
    permitted_actions: Set[str] = field(default_factory=set)
    immune:            bool     = False

    @property
    def scope_id(self) -> str:
        """Canonical identifier: ``"<tier>:<branch>"``."""
        return f"{self.tier.name}:{self.branch.name}"

    def can_perform(self, action: str) -> bool:
        """Return True iff *action* is within this scope's permitted set."""
        return action in self.permitted_actions

    def scope_hash(self) -> str:
        """SHA-256 digest of this scope's canonical declaration."""
        payload = json.dumps(
            {
                "scope_id":          self.scope_id,
                "permitted_actions": sorted(self.permitted_actions),
                "immune":            self.immune,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


# ---------------------------------------------------------------------------
# DualSovereignty
# ---------------------------------------------------------------------------


class DualSovereignty:
    """Two-tier (State / National) authority model.

    Adams' dual-sovereignty principle holds that power originates from the
    people at *both* state and national levels.  Overlapping jurisdictions
    provide "double security" against capture by any single faction.

    Parameters
    ----------
    scopes:
        Initial list of :class:`BranchScope` instances to register.
    """

    def __init__(self, scopes: Optional[List[BranchScope]] = None) -> None:
        self._scopes: Dict[str, BranchScope] = {}
        for scope in (scopes or []):
            self.register(scope)

    def register(self, scope: BranchScope) -> None:
        """Register a :class:`BranchScope`.

        Raises :class:`SubordinationError` if the scope claims immunity.
        """
        if scope.immune:
            raise SubordinationError(
                scope.scope_id,
                "No scope may claim sovereign immunity "
                "(Adams: all chartered entities are subordinate to natural law).",
            )
        self._scopes[scope.scope_id] = scope

    def resolve(self, branch: Branch, tier: SovereigntyTier) -> Optional[BranchScope]:
        """Return the registered scope for *(branch, tier)*, or ``None``."""
        return self._scopes.get(f"{tier.name}:{branch.name}")

    def authorised(self, branch: Branch, tier: SovereigntyTier, action: str) -> bool:
        """Return True iff *branch* at *tier* is authorised to perform *action*."""
        scope = self.resolve(branch, tier)
        return scope is not None and scope.can_perform(action)

    @property
    def scopes(self) -> List[BranchScope]:
        return list(self._scopes.values())


# ---------------------------------------------------------------------------
# FactionSubordination
# ---------------------------------------------------------------------------


class FactionSubordination:
    """Enforce Adams' principle that no faction stands above the law.

    Any entity — corporation, institution, or algorithm — that attempts to
    assert immunity from declared constraints is immediately flagged as a
    subordination violation.

    Parameters
    ----------
    entities:
        Initial mapping ``{entity_id: immune_flag}``.
    """

    def __init__(self, entities: Optional[Dict[str, bool]] = None) -> None:
        self._entities: Dict[str, bool] = {}
        for entity_id, immune in (entities or {}).items():
            self.register_entity(entity_id, immune)

    def register_entity(self, entity_id: str, immune: bool = False) -> None:
        """Register an entity.

        Raises :class:`SubordinationError` immediately if ``immune=True``
        (no entity may self-declare immunity at registration time).
        """
        if immune:
            raise SubordinationError(
                entity_id,
                "Entity attempted to self-declare sovereign immunity at registration.",
            )
        self._entities[entity_id] = False

    def audit(self, entity_id: str) -> bool:
        """Return True iff *entity_id* is properly subordinate (not immune).

        Raises :class:`SubordinationError` if the entity is unknown or immune.
        """
        if entity_id not in self._entities:
            raise SubordinationError(
                entity_id,
                "Entity is not registered with the accountability framework.",
            )
        if self._entities[entity_id]:
            raise SubordinationError(
                entity_id,
                "Entity claims sovereign immunity — inadmissible under natural law.",
            )
        return True

    @property
    def entity_ids(self) -> List[str]:
        return list(self._entities.keys())


# ---------------------------------------------------------------------------
# SovereignAccountability
# ---------------------------------------------------------------------------


class SovereignAccountability:
    """Orchestrator connecting Adams' structural model to TAS invariants.

    Composes :class:`DualSovereignty` and :class:`FactionSubordination` into
    a single accountability surface and exposes a UVK-compatible
    :class:`~uvk.Invariant` factory.

    Parameters
    ----------
    dual_sovereignty:
        Pre-configured :class:`DualSovereignty` instance.
    faction_subordination:
        Pre-configured :class:`FactionSubordination` instance.
    """

    #: Adams' maxim — the foundational principle of this module.
    ADAMS_MAXIM: str = (
        "No corporate, institutional, or algorithmic interest is immune to "
        "the natural law of the land.  Authority is structurally inherited, "
        "not behaviourally asserted.  A Constitution of Government once "
        "changed from Freedom, can never be restored."
    )

    def __init__(
        self,
        dual_sovereignty:      Optional[DualSovereignty]      = None,
        faction_subordination: Optional[FactionSubordination] = None,
    ) -> None:
        self.dual_sovereignty      = dual_sovereignty      or DualSovereignty()
        self.faction_subordination = faction_subordination or FactionSubordination()

    # ------------------------------------------------------------------
    # Authorisation
    # ------------------------------------------------------------------

    def authorised(
        self,
        entity_id: str,
        branch:    Branch,
        tier:      SovereigntyTier,
        action:    str,
    ) -> bool:
        """Return True iff *entity_id* is subordinate AND *branch* at *tier*
        is authorised to perform *action*.

        Raises :class:`SubordinationError` if the entity claims immunity or is
        unregistered.
        """
        self.faction_subordination.audit(entity_id)
        return self.dual_sovereignty.authorised(branch, tier, action)

    # ------------------------------------------------------------------
    # UVK Invariant factory
    # ------------------------------------------------------------------

    def make_accountability_invariant(
        self,
        entity_extractor: Callable[[Any, Any, Any], str],
        branch_extractor: Callable[[Any, Any, Any], Branch],
        tier_extractor:   Callable[[Any, Any, Any], SovereigntyTier],
        version:          str = "1.0.0",
    ) -> Invariant:
        """Return a :class:`~uvk.Invariant` that enforces sovereign accountability.

        On every UVK admission the invariant checks:

        1. The acting entity is registered and not claiming immunity.
        2. The entity's branch is authorised to perform the action.

        Parameters
        ----------
        entity_extractor:
            ``(state, action, inputs) → entity_id`` — pure, side-effect-free.
        branch_extractor:
            ``(state, action, inputs) → Branch``.
        tier_extractor:
            ``(state, action, inputs) → SovereigntyTier``.
        version:
            Invariant version string.

        Returns
        -------
        Invariant
            Named ``"sovereign:accountability"`` with the supplied version.
        """
        accountability = self

        def _check(state: Any, action: Any, inputs: Any) -> bool:
            entity_id = entity_extractor(state, action, inputs)
            branch    = branch_extractor(state, action, inputs)
            tier      = tier_extractor(state, action, inputs)
            return accountability.authorised(entity_id, branch, tier, str(action))

        return Invariant(
            name    = "sovereign:accountability",
            version = version,
            check   = _check,
        )
