"""Tests for Sovereign Accountability (Adams' structural model).

Covers:
- Branch: enum completeness
- SovereigntyTier: enum completeness
- SubordinationError: attributes, message
- BranchScope: scope_id, can_perform, scope_hash, immune guard
- DualSovereignty: register, resolve, authorised, immune guard
- FactionSubordination: register_entity, audit, immune guard
- SovereignAccountability: authorised, make_accountability_invariant, ADAMS_MAXIM
- Integration: full three-branch, two-tier pipeline with UVK invariant
"""
# © 2025 Russell Nordland | TrueAlphaSpiral (TAS) | Apache-2.0

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from sovereign_accountability import (
    Branch,
    SovereigntyTier,
    SubordinationError,
    BranchScope,
    DualSovereignty,
    FactionSubordination,
    SovereignAccountability,
)
from uvk import UVK, Invariant
from capability import CapabilityTable, Right
from wake_chain import WakeChain


# ===========================================================================
# Branch
# ===========================================================================


class TestBranch:
    """Invariant U6 — Sovereign Accountability: Branch enum completeness.

    Enforces: exactly three branches (EXECUTIVE, JUDICIAL, LEGISLATIVE) with
    distinct values exist; the enum is the structural foundation for dual-sovereignty scope checks.
    """

    def test_three_branches_defined(self):
        assert len(list(Branch)) == 3

    def test_all_branch_names_present(self):
        names = {b.name for b in Branch}
        assert names == {"EXECUTIVE", "JUDICIAL", "LEGISLATIVE"}

    def test_branches_are_distinct(self):
        values = [b.value for b in Branch]
        assert len(values) == len(set(values))


# ===========================================================================
# SovereigntyTier
# ===========================================================================


class TestSovereigntyTier:
    """Invariant U6 — Sovereign Accountability: SovereigntyTier enum completeness.

    Enforces: exactly two tiers (STATE, NATIONAL) with distinct values exist,
    enabling the dual-sovereignty (federal/state) separation model.
    """

    def test_two_tiers_defined(self):
        assert len(list(SovereigntyTier)) == 2

    def test_state_and_national_present(self):
        names = {t.name for t in SovereigntyTier}
        assert names == {"STATE", "NATIONAL"}

    def test_tiers_are_distinct(self):
        values = [t.value for t in SovereigntyTier]
        assert len(values) == len(set(values))


# ===========================================================================
# SubordinationError
# ===========================================================================


class TestSubordinationError:
    """Invariant U6 — Sovereign Accountability: SubordinationError exception contract.

    Enforces: SubordinationError carries the entity name and a detail string;
    is a subtype of Exception so governance boundaries can catch it.
    """

    def test_entity_stored(self):
        e = SubordinationError("corp_A", "claims immunity")
        assert e.entity == "corp_A"

    def test_detail_stored(self):
        e = SubordinationError("corp_A", "claims immunity")
        assert e.detail == "claims immunity"

    def test_is_exception(self):
        assert isinstance(SubordinationError("x", "y"), Exception)

    def test_message_contains_entity(self):
        e = SubordinationError("mega_corp", "above the law")
        assert "mega_corp" in str(e)


# ===========================================================================
# BranchScope
# ===========================================================================


class TestBranchScope:
    """Invariant U6 — Sovereign Accountability: BranchScope permitted-actions gate.

    Enforces: can_perform returns True iff the action is in permitted_actions;
    scope_id is deterministic as "TIER:BRANCH"; scope_hash is a deterministic
    SHA-256 over scope fields; immune=True is rejected at registration.
    """

    def _scope(self, branch=Branch.EXECUTIVE, tier=SovereigntyTier.NATIONAL,
               actions=None, immune=False):
        return BranchScope(
            branch=branch,
            tier=tier,
            permitted_actions=set(actions or []),
            immune=immune,
        )

    def test_scope_id_format(self):
        scope = self._scope()
        assert scope.scope_id == "NATIONAL:EXECUTIVE"

    def test_scope_id_state_tier(self):
        scope = self._scope(tier=SovereigntyTier.STATE)
        assert scope.scope_id == "STATE:EXECUTIVE"

    def test_can_perform_permitted_action(self):
        scope = self._scope(actions=["enforce", "administer"])
        assert scope.can_perform("enforce") is True

    def test_cannot_perform_unpermitted_action(self):
        scope = self._scope(actions=["enforce"])
        assert scope.can_perform("adjudicate") is False

    def test_can_perform_empty_set_returns_false(self):
        scope = self._scope(actions=[])
        assert scope.can_perform("anything") is False

    def test_scope_hash_is_64_hex(self):
        scope = self._scope(actions=["a", "b"])
        h = scope.scope_hash()
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_scope_hash_deterministic(self):
        s1 = self._scope(actions=["x", "y"])
        s2 = self._scope(actions=["x", "y"])
        assert s1.scope_hash() == s2.scope_hash()

    def test_scope_hash_changes_with_actions(self):
        s1 = self._scope(actions=["x"])
        s2 = self._scope(actions=["y"])
        assert s1.scope_hash() != s2.scope_hash()

    def test_immune_flag_defaults_false(self):
        scope = BranchScope(branch=Branch.JUDICIAL, tier=SovereigntyTier.STATE)
        assert scope.immune is False


# ===========================================================================
# DualSovereignty
# ===========================================================================


class TestDualSovereignty:
    """Invariant U6 — Sovereign Accountability: DualSovereignty (federal/state) model.

    Enforces: scopes are independently registered per (branch, tier) pair; immune
    scopes are rejected at registration; authorised returns True iff the action is
    in the scope's permitted_actions; state and national scopes are independent.
    """

    def _exec_scope(self, actions=None, tier=SovereigntyTier.NATIONAL):
        return BranchScope(
            branch=Branch.EXECUTIVE,
            tier=tier,
            permitted_actions=set(actions or ["enforce"]),
        )

    def test_register_adds_scope(self):
        ds = DualSovereignty()
        scope = self._exec_scope()
        ds.register(scope)
        assert ds.resolve(Branch.EXECUTIVE, SovereigntyTier.NATIONAL) is scope

    def test_register_immune_scope_raises(self):
        ds = DualSovereignty()
        immune_scope = BranchScope(
            branch=Branch.EXECUTIVE,
            tier=SovereigntyTier.NATIONAL,
            immune=True,
        )
        with pytest.raises(SubordinationError):
            ds.register(immune_scope)

    def test_resolve_unregistered_returns_none(self):
        ds = DualSovereignty()
        assert ds.resolve(Branch.JUDICIAL, SovereigntyTier.STATE) is None

    def test_authorised_with_permitted_action(self):
        ds = DualSovereignty(scopes=[self._exec_scope(actions=["enforce"])])
        assert ds.authorised(Branch.EXECUTIVE, SovereigntyTier.NATIONAL, "enforce") is True

    def test_not_authorised_with_unpermitted_action(self):
        ds = DualSovereignty(scopes=[self._exec_scope(actions=["enforce"])])
        assert ds.authorised(Branch.EXECUTIVE, SovereigntyTier.NATIONAL, "legislate") is False

    def test_not_authorised_for_unregistered_scope(self):
        ds = DualSovereignty()
        assert ds.authorised(Branch.JUDICIAL, SovereigntyTier.STATE, "adjudicate") is False

    def test_scopes_property_returns_all(self):
        ds = DualSovereignty()
        s1 = BranchScope(Branch.EXECUTIVE, SovereigntyTier.NATIONAL, permitted_actions={"a"})
        s2 = BranchScope(Branch.JUDICIAL, SovereigntyTier.STATE, permitted_actions={"b"})
        ds.register(s1)
        ds.register(s2)
        assert len(ds.scopes) == 2

    def test_initial_scopes_via_constructor(self):
        scope = self._exec_scope()
        ds = DualSovereignty(scopes=[scope])
        assert ds.resolve(Branch.EXECUTIVE, SovereigntyTier.NATIONAL) is scope

    def test_state_and_national_scopes_independent(self):
        state_scope    = BranchScope(Branch.JUDICIAL, SovereigntyTier.STATE,
                                     permitted_actions={"local_adjudicate"})
        national_scope = BranchScope(Branch.JUDICIAL, SovereigntyTier.NATIONAL,
                                     permitted_actions={"federal_adjudicate"})
        ds = DualSovereignty(scopes=[state_scope, national_scope])
        assert ds.authorised(Branch.JUDICIAL, SovereigntyTier.STATE, "local_adjudicate")
        assert not ds.authorised(Branch.JUDICIAL, SovereigntyTier.STATE, "federal_adjudicate")


# ===========================================================================
# FactionSubordination
# ===========================================================================


class TestFactionSubordination:
    """Invariant U6 — Sovereign Accountability: FactionSubordination subordination law.

    Enforces: every entity must be registered before it can be audited;
    immune entities are rejected at registration (no entity is above the law);
    unregistered entities raise SubordinationError on audit.
    """

    def test_register_entity_adds_to_roster(self):
        fs = FactionSubordination()
        fs.register_entity("corp_A")
        assert "corp_A" in fs.entity_ids

    def test_register_immune_entity_raises(self):
        fs = FactionSubordination()
        with pytest.raises(SubordinationError) as exc_info:
            fs.register_entity("mega_corp", immune=True)
        assert "mega_corp" in exc_info.value.entity

    def test_audit_registered_entity_returns_true(self):
        fs = FactionSubordination()
        fs.register_entity("entity_1")
        assert fs.audit("entity_1") is True

    def test_audit_unregistered_entity_raises(self):
        fs = FactionSubordination()
        with pytest.raises(SubordinationError):
            fs.audit("ghost_entity")

    def test_initial_entities_via_constructor(self):
        fs = FactionSubordination(entities={"corp_x": False})
        assert "corp_x" in fs.entity_ids

    def test_constructor_with_immune_entity_raises(self):
        with pytest.raises(SubordinationError):
            FactionSubordination(entities={"immune_corp": True})

    def test_entity_ids_returns_list(self):
        fs = FactionSubordination()
        fs.register_entity("a")
        fs.register_entity("b")
        assert isinstance(fs.entity_ids, list)
        assert set(fs.entity_ids) == {"a", "b"}


# ===========================================================================
# SovereignAccountability
# ===========================================================================


class TestSovereignAccountability:
    """Invariant U6 — Sovereign Accountability: combined authorisation gate.

    Enforces: authorised(entity, branch, tier, action) returns True iff the entity
    is registered AND the branch/tier scope permits the action; unregistered entities
    raise SubordinationError; ADAMS_MAXIM is a non-empty string referencing natural law.
    """

    def _build(self):
        judicial_scope = BranchScope(
            branch=Branch.JUDICIAL,
            tier=SovereigntyTier.NATIONAL,
            permitted_actions={"adjudicate", "interpret"},
        )
        ds = DualSovereignty(scopes=[judicial_scope])
        fs = FactionSubordination()
        fs.register_entity("court_A")
        return SovereignAccountability(dual_sovereignty=ds, faction_subordination=fs)

    def test_authorised_registered_entity_permitted_action(self):
        sa = self._build()
        assert sa.authorised(
            "court_A", Branch.JUDICIAL, SovereigntyTier.NATIONAL, "adjudicate"
        ) is True

    def test_authorised_returns_false_for_unpermitted_action(self):
        sa = self._build()
        assert sa.authorised(
            "court_A", Branch.JUDICIAL, SovereigntyTier.NATIONAL, "legislate"
        ) is False

    def test_authorised_raises_for_unregistered_entity(self):
        sa = self._build()
        with pytest.raises(SubordinationError):
            sa.authorised("unknown", Branch.JUDICIAL, SovereigntyTier.NATIONAL, "adjudicate")

    def test_adams_maxim_is_non_empty_string(self):
        assert isinstance(SovereignAccountability.ADAMS_MAXIM, str)
        assert len(SovereignAccountability.ADAMS_MAXIM) > 0

    def test_adams_maxim_references_natural_law(self):
        assert "natural law" in SovereignAccountability.ADAMS_MAXIM.lower()

    def test_adams_maxim_references_authority(self):
        assert "authority" in SovereignAccountability.ADAMS_MAXIM.lower()

    def test_default_construction_uses_empty_dual_sovereignty(self):
        sa = SovereignAccountability()
        assert isinstance(sa.dual_sovereignty, DualSovereignty)

    def test_default_construction_uses_empty_faction_subordination(self):
        sa = SovereignAccountability()
        assert isinstance(sa.faction_subordination, FactionSubordination)


# ===========================================================================
# make_accountability_invariant
# ===========================================================================


class TestAccountabilityInvariant:
    """Invariant U6 — Sovereign Accountability: make_accountability_invariant factory.

    Enforces: the returned Invariant passes for authorised (entity, branch, tier, action)
    tuples; fails for unpermitted actions; raises SubordinationError for unregistered
    entities — making it directly composable with UVK admission control.
    """

    def _build_sa(self):
        exec_scope = BranchScope(
            branch=Branch.EXECUTIVE,
            tier=SovereigntyTier.NATIONAL,
            permitted_actions={"enforce"},
        )
        ds = DualSovereignty(scopes=[exec_scope])
        fs = FactionSubordination()
        fs.register_entity("agent_x")
        return SovereignAccountability(dual_sovereignty=ds, faction_subordination=fs)

    def test_returns_invariant_instance(self):
        sa = self._build_sa()
        inv = sa.make_accountability_invariant(
            entity_extractor = lambda s, a, i: "agent_x",
            branch_extractor = lambda s, a, i: Branch.EXECUTIVE,
            tier_extractor   = lambda s, a, i: SovereigntyTier.NATIONAL,
        )
        assert isinstance(inv, Invariant)

    def test_invariant_named_correctly(self):
        sa = self._build_sa()
        inv = sa.make_accountability_invariant(
            entity_extractor = lambda s, a, i: "agent_x",
            branch_extractor = lambda s, a, i: Branch.EXECUTIVE,
            tier_extractor   = lambda s, a, i: SovereigntyTier.NATIONAL,
        )
        assert inv.name == "sovereign:accountability"

    def test_invariant_version_stored(self):
        sa = self._build_sa()
        inv = sa.make_accountability_invariant(
            entity_extractor = lambda s, a, i: "agent_x",
            branch_extractor = lambda s, a, i: Branch.EXECUTIVE,
            tier_extractor   = lambda s, a, i: SovereigntyTier.NATIONAL,
            version          = "2.0.0",
        )
        assert inv.version == "2.0.0"

    def test_invariant_passes_for_authorised_action(self):
        sa = self._build_sa()
        inv = sa.make_accountability_invariant(
            entity_extractor = lambda s, a, i: "agent_x",
            branch_extractor = lambda s, a, i: Branch.EXECUTIVE,
            tier_extractor   = lambda s, a, i: SovereigntyTier.NATIONAL,
        )
        assert inv.check(None, "enforce", {}) is True

    def test_invariant_fails_for_unpermitted_action(self):
        sa = self._build_sa()
        inv = sa.make_accountability_invariant(
            entity_extractor = lambda s, a, i: "agent_x",
            branch_extractor = lambda s, a, i: Branch.EXECUTIVE,
            tier_extractor   = lambda s, a, i: SovereigntyTier.NATIONAL,
        )
        assert inv.check(None, "legislate", {}) is False

    def test_invariant_raises_for_unregistered_entity(self):
        sa = self._build_sa()
        inv = sa.make_accountability_invariant(
            entity_extractor = lambda s, a, i: "unknown_entity",
            branch_extractor = lambda s, a, i: Branch.EXECUTIVE,
            tier_extractor   = lambda s, a, i: SovereigntyTier.NATIONAL,
        )
        with pytest.raises(SubordinationError):
            inv.check(None, "enforce", {})


# ===========================================================================
# Integration: three branches, two tiers, UVK invariant
# ===========================================================================


class TestSovereignAccountabilityIntegration:
    """Integration: three branches, two tiers, UVK invariant (U1+U6).

    Enforces: EXECUTIVE/JUDICIAL/LEGISLATIVE branches and STATE/NATIONAL tiers operate
    independently; cross-branch actions are denied; UVK.admit() is ADMITTED for
    authorised (entity, branch, tier, action) and DENIED_INVARIANT for unpermitted ones.
    """

    def _build_full_system(self):
        exec_national  = BranchScope(Branch.EXECUTIVE,   SovereigntyTier.NATIONAL,
                                     permitted_actions={"enforce", "administer"})
        judic_national = BranchScope(Branch.JUDICIAL,    SovereigntyTier.NATIONAL,
                                     permitted_actions={"adjudicate", "interpret"})
        legis_national = BranchScope(Branch.LEGISLATIVE, SovereigntyTier.NATIONAL,
                                     permitted_actions={"legislate", "charter"})
        exec_state     = BranchScope(Branch.EXECUTIVE,   SovereigntyTier.STATE,
                                     permitted_actions={"local_enforce"})

        ds = DualSovereignty(scopes=[
            exec_national, judic_national, legis_national, exec_state
        ])
        fs = FactionSubordination()
        for eid in ["agent_exec", "agent_judic", "agent_legis", "corp_A"]:
            fs.register_entity(eid)

        return SovereignAccountability(dual_sovereignty=ds, faction_subordination=fs)

    def test_executive_can_enforce_nationally(self):
        sa = self._build_full_system()
        assert sa.authorised("agent_exec", Branch.EXECUTIVE,
                             SovereigntyTier.NATIONAL, "enforce") is True

    def test_executive_cannot_legislate(self):
        sa = self._build_full_system()
        assert sa.authorised("agent_exec", Branch.EXECUTIVE,
                             SovereigntyTier.NATIONAL, "legislate") is False

    def test_judicial_can_adjudicate(self):
        sa = self._build_full_system()
        assert sa.authorised("agent_judic", Branch.JUDICIAL,
                             SovereigntyTier.NATIONAL, "adjudicate") is True

    def test_legislative_can_charter(self):
        sa = self._build_full_system()
        assert sa.authorised("agent_legis", Branch.LEGISLATIVE,
                             SovereigntyTier.NATIONAL, "charter") is True

    def test_corporate_entity_cannot_claim_immunity(self):
        with pytest.raises(SubordinationError):
            FactionSubordination(entities={"mega_corp": True})

    def test_state_scope_provides_double_security(self):
        sa = self._build_full_system()
        assert sa.authorised("agent_exec", Branch.EXECUTIVE,
                             SovereigntyTier.STATE, "local_enforce") is True
        assert sa.authorised("agent_exec", Branch.EXECUTIVE,
                             SovereigntyTier.STATE, "enforce") is False

    def test_uvk_integration_with_accountability_invariant(self):
        sa = self._build_full_system()
        inv = sa.make_accountability_invariant(
            entity_extractor = lambda s, a, i: i.get("entity", ""),
            branch_extractor = lambda s, a, i: i.get("branch", Branch.EXECUTIVE),
            tier_extractor   = lambda s, a, i: i.get("tier", SovereigntyTier.NATIONAL),
        )

        wake      = WakeChain()
        cap_table = CapabilityTable()
        cap       = cap_table.retype("exec_cap", Right.EXECUTE)
        uvk       = UVK(capability_table=cap_table, wake_chain=wake, invariants=[inv])

        result = uvk.admit(
            capability     = cap,
            required_right = Right.EXECUTE,
            action         = "enforce",
            inputs         = {
                "entity": "agent_exec",
                "branch": Branch.EXECUTIVE,
                "tier":   SovereigntyTier.NATIONAL,
            },
        )
        assert result.admitted is True

    def test_uvk_denies_unpermitted_action(self):
        sa = self._build_full_system()
        inv = sa.make_accountability_invariant(
            entity_extractor = lambda s, a, i: i.get("entity", ""),
            branch_extractor = lambda s, a, i: i.get("branch", Branch.EXECUTIVE),
            tier_extractor   = lambda s, a, i: i.get("tier", SovereigntyTier.NATIONAL),
        )

        wake      = WakeChain()
        cap_table = CapabilityTable()
        cap       = cap_table.retype("exec_cap", Right.EXECUTE)
        uvk       = UVK(capability_table=cap_table, wake_chain=wake, invariants=[inv])

        result = uvk.admit(
            capability     = cap,
            required_right = Right.EXECUTE,
            action         = "legislate",
            inputs         = {
                "entity": "agent_exec",
                "branch": Branch.EXECUTIVE,
                "tier":   SovereigntyTier.NATIONAL,
            },
        )
        assert result.admitted is False
