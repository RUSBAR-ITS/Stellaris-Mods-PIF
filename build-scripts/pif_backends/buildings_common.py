#!/usr/bin/env python3
"""
Shared Stage-4 building backend logic for PIF tooling.

This module contains only deterministic classification / transformation rules.
It deliberately does not infer meaning from comments or vanilla variable names;
classification is based on AST keys and resolved scalar context.
"""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from pif_stellaris import Atom, Block, Stmt, clone_node, render_file, resolve_atom_number, sanitize_identifier, top_level_stmts


CANONICAL_BUILDING_CATEGORIES = [
    "building_config",
    "availability",
    "economy",
    "lifecycle",
    "jobs",
    "country_jobs",
    "economic_modifiers",
    "pop_modifiers",
    "planet_state",
    "tpm",
    "ai",
]

BUILDING_CATEGORY_DISPLAY = {
    "metadata": "METADATA",
    "building_config": "BUILDING_CONFIG",
    "availability": "AVAILABILITY",
    "economy": "ECONOMY",
    "lifecycle": "LIFECYCLE",
    "jobs": "JOBS",
    "country_jobs": "COUNTRY_JOBS",
    "economic_modifiers": "ECONOMIC_MODIFIERS",
    "pop_modifiers": "POP_MODIFIERS",
    "planet_state": "PLANET_STATE",
    "tpm": "TPM",
    "ai": "AI",
    "unknown": "UNKNOWN",
}

BUILDING_METADATA_KEYS = {
    "category",
    "owner_type",
    "capital",
    "capital_tier",
    "icon",
    "ruined_icon",
    "desc",
    "triggered_desc",
    "custom_tooltip",
    "position_priority",
    "base_buildtime",
    "auto_generate_description",
    "is_essential",
    "skip_automation_upgrading",
}
BUILDING_CONFIG_KEYS = {"building_sets"}
BUILDING_AVAILABILITY_KEYS = {
    "potential",
    "allow",
    "can_build",
    "prerequisites",
    "show_tech_unlock_if",
    "show_in_tech",
    "planet_limit",
    "empire_limit",
    "base_cap_amount",
    "district_limit",
}
BUILDING_ECONOMY_KEYS = {"resources"}
BUILDING_LIFECYCLE_KEYS = {
    "can_demolish",
    "can_be_ruined",
    "can_be_disabled",
    "destroy_trigger",
    "convert_to",
    "upgrades",
    "on_queued",
    "on_unqueued",
    "on_built",
    "on_destroy",
    "on_repaired",
    "on_enabled",
    # Documented but unused in the vanilla 4.3.7 baseline.
    "abort_trigger",
    "abort_construction_trigger",
    "ruined_trigger",
}
BUILDING_AI_KEYS = {
    "ai_resource_production",
    "ai_weight",
    "ai_weight_coefficient",
    "additional_ai_weight",
    "ai_estimate_without_unemployment",
    "exempt_from_ai_planet_specialization",
    "custom_storm_ai_weight",
}
BUILDING_PLANET_STATE_KEYS = {"planetary_ftl_inhibitor"}
BUILDING_MODIFIER_CARRIERS = {
    "planet_modifier",
    "triggered_planet_modifier",
    "country_modifier",
    "triggered_country_modifier",
    "system_modifier",
    "triggered_planet_pop_group_modifier_for_all",
    "triggered_planet_pop_group_modifier_for_species",
    "army_modifier",
}
STATIC_BUILDING_MODIFIER_MAP = {
    "planet_modifier": "triggered_planet_modifier",
    "country_modifier": "triggered_country_modifier",
}
MODIFIER_TECHNICAL_KEYS = {"potential", "key", "mult", "trigger", "modifier"}

VARIABLE_DOMAIN_FILE_NAMES = {
    "construction": "pif_buildings_construction_variables.txt",
    "cost": "pif_buildings_cost_variables.txt",
    "upkeep": "pif_buildings_upkeep_variables.txt",
    "limits": "pif_buildings_limits_variables.txt",
    "availability_thresholds": "pif_buildings_availability_thresholds_variables.txt",
    "jobs": "pif_buildings_jobs_variables.txt",
    "country_jobs": "pif_buildings_country_jobs_variables.txt",
    "economic_modifiers": "pif_buildings_economic_modifiers_variables.txt",
    "pop_modifiers": "pif_buildings_pop_modifiers_variables.txt",
    "planet_state": "pif_buildings_planet_state_variables.txt",
    "ai": "pif_buildings_ai_variables.txt",
    "tpm": "pif_buildings_tpm_variables.txt",
}
VARIABLE_DOMAIN_TITLES = {key: key.upper() for key in VARIABLE_DOMAIN_FILE_NAMES}

LOCALIZATION_TOP_KEYS = {"desc", "triggered_desc", "triggered_name", "triggered_flavor_desc", "custom_tooltip"}
STRUCTURAL_NUMERIC_KEYS = {"capital_tier", "position_priority"}
TECHNICAL_COUNTER_KEYS = {"count", "value"}
SIGNIFICANT_AVAILABILITY_THRESHOLD_KEYS = {"sapient_pop_amount", "pop_amount", "free_amenities", "planet_stability"}
SIGNIFICANT_TPM_KEYS = {
    "monthly_loyalty",
    "auto_mod_monthly_add",
    "commercial_pact_mult",
    "storm_attraction_field_modifier",
    "country_naval_cap_add",
    "envoys_add",
    "country_edict_fund_add",
    "leader_lifespan_add",
    "starbase_defense_platform_capacity_add",
    "country_resource_max_energy_add",
    "country_resource_max_minerals_add",
    "country_resource_max_food_add",
    "starbase_shipyard_build_speed_mult",
}
RESOURCE_KEYS = {
    "energy", "minerals", "food", "alloys", "consumer_goods", "unity", "influence", "society_research",
    "physics_research", "engineering_research", "volatile_motes", "exotic_gases", "rare_crystals",
    "sr_dark_matter", "nanites", "minor_artifacts", "biomass", "astral_threads", "time", "days",
}


@dataclass(frozen=True)
class VariableClassification:
    """Semantic variable-domain classification for one meaningful scalar."""

    domain: str
    function_key: str
    purpose: str


@dataclass
class VariableUse:
    """One generated-variable usage location."""

    building: str
    used_in: str
    path: str


@dataclass
class PifVariable:
    """Generated PIF scripted variable."""

    name: str
    value: str
    domain: str
    building: str
    purpose: str
    uses: List[VariableUse] = field(default_factory=list)


def building_category_for_param(param: str) -> str:
    """Return the PIF building object category for a top-level parameter name."""
    if param in BUILDING_METADATA_KEYS:
        return "metadata"
    if param in BUILDING_CONFIG_KEYS:
        return "building_config"
    if param in BUILDING_AVAILABILITY_KEYS:
        return "availability"
    if param in BUILDING_ECONOMY_KEYS:
        return "economy"
    if param in BUILDING_LIFECYCLE_KEYS:
        return "lifecycle"
    if param in BUILDING_AI_KEYS:
        return "ai"
    if param in BUILDING_PLANET_STATE_KEYS:
        return "planet_state"
    if param in BUILDING_MODIFIER_CARRIERS:
        return "tpm"
    return "unknown"


def normalize_building_static_modifier(stmt: Stmt) -> List[Stmt]:
    """Normalize static building modifier carriers to triggered carriers."""
    if stmt.key not in STATIC_BUILDING_MODIFIER_MAP or not isinstance(stmt.value, Block):
        return [clone_node(stmt)]
    body = Block([
        Stmt("potential", "=", Block([Stmt("always", "=", Atom("yes"))])),
        *[clone_node(item) for item in stmt.value.items],
    ])
    return [Stmt(STATIC_BUILDING_MODIFIER_MAP[stmt.key], "=", body)]


def normalize_building_stmt(stmt: Stmt) -> List[Stmt]:
    """Normalize one building statement using Stage-4 accepted rules."""
    return normalize_building_static_modifier(stmt)


def _collect_modifier_keys_from_block(block: Block) -> List[str]:
    """Collect gameplay modifier keys from a modifier carrier block."""
    keys: List[str] = []
    for item in block.items:
        if not isinstance(item, Stmt):
            continue
        if item.key == "modifier" and isinstance(item.value, Block):
            keys.extend(_collect_modifier_keys_from_block(item.value))
            continue
        if item.key in MODIFIER_TECHNICAL_KEYS:
            continue
        keys.append(item.key)
    return keys


def _is_job_key(key: str) -> bool:
    return bool(re.match(r"^job_.+_(?:add|mult|upkeep_add|upkeep_mult|produces_add|produces_mult)$", key)) or key.startswith("job_")


def _is_economic_key(key: str) -> bool:
    low = key.lower()
    if low in RESOURCE_KEYS:
        return True
    if low.startswith("planet_jobs_"):
        return True
    if "_produces_" in low or low.endswith("_produces_add") or low.endswith("_produces_mult"):
        return True
    if "_upkeep_" in low or low.endswith("_upkeep_add") or low.endswith("_upkeep_mult"):
        return True
    economic_markers = [
        "miner", "farmer", "technician", "artisan", "metallurgist", "researcher", "bureaucrat", "priest",
        "coordinator", "trader", "clerk", "trade_value", "resource_max", "unity_produces", "research_produces",
        "consumer_goods", "alloys", "minerals", "energy", "food",
    ]
    return any(marker in low for marker in economic_markers) and (
        low.startswith("planet_") or low.startswith("country_") or low.startswith("branch_office_")
    )


def _is_pop_key(key: str) -> bool:
    low = key.lower()
    markers = [
        "pop_", "growth", "happiness", "habitability", "workforce", "assembly", "migration", "logistic",
        "species", "demotion", "resettlement", "amenities_usage", "housing_usage",
    ]
    return any(marker in low for marker in markers)


def _is_planet_state_key(key: str) -> bool:
    low = key.lower()
    markers = [
        "housing", "amenities", "crime", "stability", "max_district", "max_branch_office", "defense_armies",
        "orbital_bombardment", "army_starting_experience", "ftl_inhibitor", "building_build_speed",
        "decision_enact_speed", "building_slot", "max_building", "district_slot",
    ]
    return any(marker in low for marker in markers)


def semantic_category_for_modifier_key(key: str, carrier_key: str) -> str:
    """Return the modifier semantic category for one gameplay modifier key."""
    if _is_job_key(key):
        if carrier_key in {"country_modifier", "triggered_country_modifier"}:
            return "country_jobs"
        return "jobs"
    if _is_pop_key(key):
        return "pop_modifiers"
    if _is_planet_state_key(key):
        return "planet_state"
    if _is_economic_key(key):
        return "economic_modifiers"
    return "tpm"


def classify_modifier_stmt(stmt: Stmt) -> str:
    """Classify a modifier carrier by its direct gameplay contents.

    If a carrier mixes multiple semantic categories, the whole carrier stays in
    fallback TPM.  The block is intentionally not split internally.
    """
    if not isinstance(stmt.value, Block):
        return "tpm"
    keys = _collect_modifier_keys_from_block(stmt.value)
    if not keys:
        return "tpm"
    categories = {semantic_category_for_modifier_key(key, stmt.key) for key in keys}
    return next(iter(categories)) if len(categories) == 1 else "tpm"


def classify_building_stmt(stmt: Stmt) -> str:
    """Classify one top-level building statement for Stage-4 buckets."""
    normalized = normalize_building_stmt(stmt)
    categories = []
    for out_stmt in normalized:
        if out_stmt.key in {"triggered_planet_modifier", "triggered_country_modifier", "system_modifier", "triggered_planet_pop_group_modifier_for_all", "triggered_planet_pop_group_modifier_for_species", "army_modifier"}:
            categories.append(classify_modifier_stmt(out_stmt))
        else:
            categories.append(building_category_for_param(out_stmt.key))
    non_unknown = [cat for cat in categories if cat != "unknown"]
    if not non_unknown:
        return "unknown"
    return non_unknown[0] if len(set(non_unknown)) == 1 else "tpm"


def split_building_statement(stmt: Stmt) -> List[Tuple[str, Stmt]]:
    """Normalize and split one expanded building statement into category pairs."""
    out: List[Tuple[str, Stmt]] = []
    for normalized in normalize_building_stmt(stmt):
        category = classify_building_stmt(normalized)
        out.append((category, normalized))
    return out


def sibling_modifier_key(block: Block) -> Optional[str]:
    """Return the first gameplay modifier key beside scalar controls in a block."""
    keys = _collect_modifier_keys_from_block(block)
    return keys[0] if keys else None


def classify_variable_path(path: List[str], current_key: str, sibling_key: Optional[str]) -> VariableClassification | None:
    """Classify one numeric scalar as a meaningful building tuning variable.

    Returning None keeps the scalar literal.  The classifier deliberately ignores
    boolean flags, structural identity values, localization selectors and pure
    control-flow counters.
    """
    if not path:
        return None
    top = path[0]
    path_set = set(path)
    path_text = ".".join(path)

    if top in LOCALIZATION_TOP_KEYS or any(key in LOCALIZATION_TOP_KEYS for key in path):
        return None
    if current_key in STRUCTURAL_NUMERIC_KEYS or any(key in STRUCTURAL_NUMERIC_KEYS for key in path):
        return None
    if current_key.startswith("value:"):
        return None

    if current_key == "base_buildtime":
        return VariableClassification("construction", "base_buildtime", "Building construction time in days")

    if "resources" in path_set and "cost" in path_set:
        return VariableClassification("cost", f"cost_{current_key}", f"Building construction cost in {current_key}")
    if "resources" in path_set and "upkeep" in path_set:
        return VariableClassification("upkeep", f"upkeep_{current_key}", f"Building upkeep in {current_key}")
    if "resources" in path_set and "produces" in path_set:
        return VariableClassification("economic_modifiers", f"produces_{current_key}", f"Building direct production in {current_key}")

    if current_key in {"planet_limit", "empire_limit", "base_cap_amount", "district_limit"} or path_set & {"planet_limit", "empire_limit", "base_cap_amount", "district_limit"}:
        return VariableClassification("limits", current_key, f"Building limit/cap value: {path_text}")

    if current_key in SIGNIFICANT_AVAILABILITY_THRESHOLD_KEYS:
        return VariableClassification("availability_thresholds", current_key, f"Building availability threshold: {current_key}")

    if "ai_resource_production" in path_set:
        return VariableClassification("ai", current_key, f"AI resource-production hint: {current_key}")
    if top in BUILDING_AI_KEYS or any(key in BUILDING_AI_KEYS for key in path):
        if current_key in {"weight", "factor", "add", "mult", "ai_weight_coefficient", "additional_ai_weight"} or current_key in RESOURCE_KEYS or current_key.startswith("ai_"):
            return VariableClassification("ai", current_key, f"AI tuning value: {path_text}")
        return None

    modifier_key = sibling_key if current_key in {"mult", "factor", "add"} and sibling_key else current_key
    modifier_category = semantic_category_for_modifier_key(modifier_key, "triggered_country_modifier" if "triggered_country_modifier" in path_set or "country_modifier" in path_set else "triggered_planet_modifier")

    if modifier_key in {"planet_building_build_speed_mult", "planet_decision_enact_speed_mult"}:
        return VariableClassification("construction", modifier_key, f"Construction/state speed modifier: {modifier_key}")
    if modifier_category == "jobs":
        return VariableClassification("jobs", modifier_key, f"Building job value: {modifier_key}")
    if modifier_category == "country_jobs":
        return VariableClassification("country_jobs", modifier_key, f"Building country-scope job value: {modifier_key}")
    if modifier_category == "economic_modifiers":
        return VariableClassification("economic_modifiers", modifier_key, f"Building economic modifier: {modifier_key}")
    if modifier_category == "pop_modifiers":
        return VariableClassification("pop_modifiers", modifier_key, f"Building pop modifier: {modifier_key}")
    if modifier_category == "planet_state":
        return VariableClassification("planet_state", modifier_key, f"Building planet-state modifier: {modifier_key}")

    if modifier_key in SIGNIFICANT_TPM_KEYS:
        return VariableClassification("tpm", modifier_key, f"Building fallback gameplay modifier: {modifier_key}")

    return None


class BuildingVariableAllocator:
    """Allocate object-specific building PIF variables."""

    def __init__(self, building_key: str, variables: Dict[str, str]):
        self.building_key = building_key
        self.source_variables = variables
        self.by_signature: Dict[Tuple[str, str, str], PifVariable] = {}
        self.counter_by_domain: Dict[str, int] = defaultdict(int)

    def resolve(self, atom: Atom) -> Optional[str]:
        return resolve_atom_number(atom, self.source_variables)

    def allocate(self, value: str, classification: VariableClassification, used_in: str, path: str) -> Atom:
        signature = (classification.domain, classification.function_key, value)
        var = self.by_signature.get(signature)
        if var is None:
            self.counter_by_domain[classification.domain] += 1
            slug = sanitize_identifier(classification.function_key)
            if len(slug) > 72:
                slug = slug[:72].rstrip("_")
            name = (
                f"@pif_{sanitize_identifier(self.building_key)}_"
                f"{sanitize_identifier(classification.domain)}_{slug}_{self.counter_by_domain[classification.domain]}"
            )
            var = PifVariable(
                name=name,
                value=value,
                domain=classification.domain,
                building=self.building_key,
                purpose=classification.purpose,
            )
            self.by_signature[signature] = var
        var.uses.append(VariableUse(building=self.building_key, used_in=used_in, path=path))
        return Atom(var.name, quoted=False)

    def replace(self, node: Any, used_in: str, path: Optional[List[str]] = None, sibling_key: Optional[str] = None) -> Any:
        """Replace meaningful numeric scalar atoms with generated variables."""
        path = path or []
        if isinstance(node, Atom):
            value = self.resolve(node)
            if value is None:
                return clone_node(node)
            current_key = path[-1] if path else "value"
            cls = classify_variable_path(path, current_key, sibling_key)
            if cls is None:
                # Do not keep vanilla @variables in generated PIF files.  If a
                # resolved scalar is intentionally not exposed as a PIF tuning
                # variable, render its resolved vanilla literal instead.
                return Atom(value, quoted=False)
            return self.allocate(value, cls, used_in, ".".join(path))
        if isinstance(node, Stmt):
            return Stmt(node.key, node.op, self.replace(node.value, used_in, path + [node.key], sibling_key))
        if isinstance(node, Block):
            block_sibling_key = sibling_modifier_key(node)
            out: List[Any] = []
            counters: Dict[str, int] = defaultdict(int)
            for item in node.items:
                if isinstance(item, Stmt):
                    counters[item.key] += 1
                    key_for_path = item.key if counters[item.key] == 1 else f"{item.key}_{counters[item.key]}"
                    out.append(self.replace(item, used_in, path + [key_for_path], block_sibling_key))
                else:
                    out.append(self.replace(item, used_in, path, block_sibling_key))
            return Block(out)
        return clone_node(node)

    def generated_variables(self) -> List[PifVariable]:
        return sorted(self.by_signature.values(), key=lambda v: (v.domain, v.building, v.name))


def variable_files_text(variables: List[PifVariable]) -> Dict[str, str]:
    """Render all building variable files grouped by object."""
    by_domain: Dict[str, Dict[str, List[PifVariable]]] = defaultdict(lambda: defaultdict(list))
    for var in variables:
        by_domain[var.domain][var.building].append(var)

    rendered: Dict[str, str] = {}
    for domain, file_name in VARIABLE_DOMAIN_FILE_NAMES.items():
        lines = [
            "# Planetary Infrastructure Framework (PIF)",
            f"# Building variables: {VARIABLE_DOMAIN_TITLES[domain]}",
            "# Values are resolved from the Stellaris 4.3.7 vanilla buildings baseline.",
            "# Variables are grouped by building object and are intentionally object-specific.",
            "",
        ]
        if domain not in by_domain:
            lines.append("# No variables were generated for this domain in the current vanilla baseline.")
        for building in sorted(by_domain.get(domain, {})):
            lines.append("# -----------------------------------------------------------------------------")
            lines.append(f"# {building}")
            lines.append("# -----------------------------------------------------------------------------")
            for var in sorted(by_domain[domain][building], key=lambda v: v.name):
                uses = sorted({use.used_in for use in var.uses})
                lines.append(f"# Controls: {var.purpose}.")
                lines.append(f"# Used in: {', '.join(uses)}")
                lines.append(f"{var.name} = {var.value}")
                lines.append("")
        rendered[file_name] = "\n".join(lines).rstrip() + "\n"
    return rendered


def render_category_script(items: List[Stmt], empty_comment: str) -> str:
    """Render a category script or an explicit empty hook comment."""
    if not items:
        return f"# {empty_comment}\n"
    return render_file(Block(items))
