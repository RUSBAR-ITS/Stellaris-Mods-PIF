#!/usr/bin/env python3
"""
Shared Stage-5 pop job backend logic for PIF tooling.

Rules in this module are deterministic and AST-based.  They do not infer
behavior from comments or variable names beyond the key names that Stellaris
itself uses for job definitions and modifier entries.
"""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from pif_stellaris import Atom, Block, Stmt, clone_node, render_file, resolve_atom_number, sanitize_identifier, top_level_stmts


CANONICAL_JOB_CATEGORIES = [
    "swap",
    "availability",
    "pop_config",
    "economy",
    "planet_state",
    "country_modifiers",
    "pop_modifiers",
    "economic_modifiers",
    "tpm",
]

JOB_CATEGORY_DISPLAY = {
    "metadata": "METADATA",
    "swap": "SWAP",
    "availability": "AVAILABILITY",
    "pop_config": "POP_CONFIG",
    "economy": "ECONOMY",
    "planet_state": "PLANET_STATE",
    "country_modifiers": "COUNTRY_MODIFIERS",
    "pop_modifiers": "POP_MODIFIERS",
    "economic_modifiers": "ECONOMIC_MODIFIERS",
    "tpm": "TPM",
    "unknown": "UNKNOWN",
}

JOB_METADATA_KEYS = {"category", "purge"}
JOB_SWAP_KEYS = {"swappable_data"}
JOB_AVAILABILITY_KEYS = {"possible", "possible_pre_triggers", "possible_precalc", "is_capped_by_modifier"}
JOB_POP_CONFIG_KEYS = {
    "weight",
    "tags",
    "triggered_tags",
    "promotion",
    "demotion",
    "auto_trait_prio",
    "can_set_priority",
    "first_come_first_served",
    "contributes_to_diplo_weight",
    "ignores_sapience",
    "count_as_available_for_ai",
    "can_be_automated",
    "allow_only_same_rank_pops",
    "exempt_from_ai_amenity_prioritization",
    "auto_generate_description",
}
JOB_ECONOMY_KEYS = {"resources", "overlord_resources"}
JOB_MODIFIER_CARRIERS = {
    "planet_modifier",
    "triggered_planet_modifier",
    "country_modifier",
    "triggered_country_modifier",
    "system_modifier",
    "triggered_planet_pop_group_modifier_for_all",
    "triggered_planet_pop_group_modifier_for_species",
}
STATIC_JOB_MODIFIER_MAP = {
    "planet_modifier": "triggered_planet_modifier",
    "country_modifier": "triggered_country_modifier",
}
MODIFIER_TECHNICAL_KEYS = {"potential", "key", "mult", "trigger", "modifier", "inline_script"}
TOP_LEVEL_BOOLEAN_FLAGS = {
    "is_capped_by_modifier",
    "can_set_priority",
    "first_come_first_served",
    "contributes_to_diplo_weight",
    "ignores_sapience",
    "count_as_available_for_ai",
    "can_be_automated",
    "allow_only_same_rank_pops",
    "exempt_from_ai_amenity_prioritization",
    "auto_generate_description",
}

VARIABLE_DOMAIN_FILE_NAMES = {
    "job_weight": "pif_jobs_weight_variables.txt",
    "job_output": "pif_jobs_output_variables.txt",
    "job_upkeep": "pif_jobs_upkeep_variables.txt",
    "job_flags": "pif_jobs_flags_variables.txt",
    "planet_state": "pif_jobs_planet_state_variables.txt",
    "promotion": "pif_jobs_promotion_variables.txt",
    "demotion": "pif_jobs_demotion_variables.txt",
    "country_modifiers": "pif_jobs_country_modifiers_variables.txt",
    "overlord_output": "pif_jobs_overlord_output_variables.txt",
    "pop_modifiers": "pif_jobs_pop_modifiers_variables.txt",
    "economic_modifiers": "pif_jobs_economic_modifiers_variables.txt",
    "tpm": "pif_jobs_tpm_variables.txt",
}
VARIABLE_DOMAIN_TITLES = {key: key.upper() for key in VARIABLE_DOMAIN_FILE_NAMES}

RESOURCE_KEYS = {
    "energy", "minerals", "food", "alloys", "consumer_goods", "unity", "influence", "society_research",
    "physics_research", "engineering_research", "volatile_motes", "exotic_gases", "rare_crystals",
    "sr_dark_matter", "sr_zro", "sr_living_metal", "nanites", "minor_artifacts", "biomass",
    "astral_threads", "trade", "trade_value", "amenities",
}
WEIGHT_AMOUNT_KEYS = {"weight", "base", "factor", "add", "mult"}
PROMOTION_AMOUNT_KEYS = {"time"}
DEMOTION_AMOUNT_KEYS = {"time"}


@dataclass(frozen=True)
class VariableClassification:
    """Semantic variable-domain classification for one meaningful job value."""

    domain: str
    function_key: str
    purpose: str


@dataclass
class VariableUse:
    """One generated-variable usage location."""

    job: str
    used_in: str
    path: str


@dataclass
class PifVariable:
    """Generated PIF scripted variable."""

    name: str
    value: str
    domain: str
    job: str
    purpose: str
    uses: List[VariableUse] = field(default_factory=list)


def job_category_for_param(param: str) -> str:
    """Return the PIF job object category for a top-level parameter name."""
    if param in JOB_METADATA_KEYS:
        return "metadata"
    if param in JOB_SWAP_KEYS:
        return "swap"
    if param in JOB_AVAILABILITY_KEYS:
        return "availability"
    if param in JOB_POP_CONFIG_KEYS:
        return "pop_config"
    if param in JOB_ECONOMY_KEYS:
        return "economy"
    if param in JOB_MODIFIER_CARRIERS:
        return "tpm"
    return "unknown"


def normalize_job_static_modifier(stmt: Stmt) -> List[Stmt]:
    """Normalize static job modifier carriers to triggered carriers."""
    if stmt.key not in STATIC_JOB_MODIFIER_MAP or not isinstance(stmt.value, Block):
        return [clone_node(stmt)]
    body = Block([
        Stmt("potential", "=", Block([Stmt("always", "=", Atom("yes"))])),
        *[clone_node(item) for item in stmt.value.items],
    ])
    return [Stmt(STATIC_JOB_MODIFIER_MAP[stmt.key], "=", body)]


def normalize_job_stmt(stmt: Stmt) -> List[Stmt]:
    """Normalize one job statement using Stage-5 accepted rules."""
    return normalize_job_static_modifier(stmt)


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
    if low in {"trade_value_add", "trade_value_mult", "branch_office_value_mult", "branch_office_criminal_syndicate_value_add"}:
        return True
    return False


def _is_planet_state_key(key: str) -> bool:
    low = key.lower()
    markers = [
        "planet_amenities", "planet_crime", "planet_stability", "planet_defense_armies",
        "planet_building", "planet_resettlement", "planet_housing", "planet_immigration", "planet_emigration",
    ]
    return any(low.startswith(marker) for marker in markers)


def _is_pop_key(key: str) -> bool:
    low = key.lower()
    if low in {"logistic_growth_mult", "bonus_pop_growth", "bonus_pop_growth_mult", "pop_government_ethic_attraction"}:
        return True
    if low.startswith("pop_") or low.startswith("planet_pop") or low.startswith("planet_pops"):
        return True
    return False


def _is_country_key(key: str) -> bool:
    low = key.lower()
    if low in {"diplo_weight_mult", "psionic_aura_effectiveness_mult"}:
        return True
    markers = ["country_", "ship_", "starbase_", "leader_", "pop_factions", "biomorphosis_", "species_leader"]
    return any(low.startswith(marker) for marker in markers)


def semantic_category_for_modifier_key(key: str, carrier_key: str) -> str:
    """Return the semantic category for one job modifier key."""
    if carrier_key in {"triggered_country_modifier", "country_modifier"}:
        return "country_modifiers"
    if carrier_key == "system_modifier":
        return "tpm"
    if carrier_key in {"triggered_planet_pop_group_modifier_for_species", "triggered_planet_pop_group_modifier_for_all"}:
        return "pop_modifiers"
    if _is_economic_key(key):
        return "economic_modifiers"
    if _is_planet_state_key(key):
        return "planet_state"
    if _is_pop_key(key):
        return "pop_modifiers"
    if _is_country_key(key):
        return "country_modifiers"
    return "tpm"


def classify_modifier_stmt(stmt: Stmt) -> str:
    """Classify a modifier carrier by its direct gameplay contents.

    Mixed carriers remain in fallback TPM.  The carrier block is intentionally
    not split internally because potential/key/mult may apply to all entries.
    """
    if not isinstance(stmt.value, Block):
        return "tpm"
    keys = _collect_modifier_keys_from_block(stmt.value)
    if not keys:
        return "tpm"
    categories = {semantic_category_for_modifier_key(key, stmt.key) for key in keys}
    return next(iter(categories)) if len(categories) == 1 else "tpm"


def classify_job_stmt(stmt: Stmt) -> str:
    """Classify one top-level job statement for Stage-5 buckets."""
    normalized = normalize_job_stmt(stmt)
    categories = []
    for out_stmt in normalized:
        if out_stmt.key in {"triggered_planet_modifier", "triggered_country_modifier", "system_modifier", "triggered_planet_pop_group_modifier_for_all", "triggered_planet_pop_group_modifier_for_species"}:
            categories.append(classify_modifier_stmt(out_stmt))
        else:
            categories.append(job_category_for_param(out_stmt.key))
    non_unknown = [cat for cat in categories if cat != "unknown"]
    if not non_unknown:
        return "unknown"
    return non_unknown[0] if len(set(non_unknown)) == 1 else "tpm"


def split_job_statement(stmt: Stmt) -> List[Tuple[str, Stmt]]:
    """Normalize and split one expanded job statement into category pairs."""
    out: List[Tuple[str, Stmt]] = []
    for normalized in normalize_job_stmt(stmt):
        category = classify_job_stmt(normalized)
        out.append((category, normalized))
    return out


def sibling_modifier_key(block: Block) -> Optional[str]:
    """Return the first gameplay modifier key beside scalar controls in a block."""
    keys = _collect_modifier_keys_from_block(block)
    return keys[0] if keys else None


def _is_bool(value: str) -> bool:
    return value in {"yes", "no"}


def classify_variable_path(path: List[str], current_key: str, sibling_key: Optional[str], category: Optional[str], atom_value: str) -> Optional[VariableClassification]:
    """Classify one scalar/flag as a meaningful Stage-5 job variable."""
    if not path:
        return None
    top = path[0]
    path_set = set(path)
    path_text = ".".join(path)

    if _is_bool(atom_value):
        if len(path) == 1 and current_key in TOP_LEVEL_BOOLEAN_FLAGS:
            return VariableClassification("job_flags", current_key, f"Top-level job boolean flag: {current_key}")
        return None

    if atom_value.startswith("value:"):
        return None

    if top == "resources":
        if "produces" in path_set:
            return VariableClassification("job_output", f"output_{current_key}", f"Job resource output in {current_key}")
        if "upkeep" in path_set:
            return VariableClassification("job_upkeep", f"upkeep_{current_key}", f"Job resource upkeep in {current_key}")
    if top == "overlord_resources":
        if "produces" in path_set:
            return VariableClassification("overlord_output", f"overlord_output_{current_key}", f"Job resource output for overlord in {current_key}")
        if "upkeep" in path_set:
            # The 4.3.7 baseline currently has no meaningful overlord upkeep values.
            return VariableClassification("tpm", f"overlord_upkeep_{current_key}", f"Fallback overlord upkeep in {current_key}")

    if top == "weight" and current_key in WEIGHT_AMOUNT_KEYS:
        return VariableClassification("job_weight", current_key, f"Job assignment weight value: {path_text}")
    if top == "promotion" and current_key in PROMOTION_AMOUNT_KEYS:
        return VariableClassification("promotion", current_key, "Job promotion time")
    if top == "demotion" and current_key in DEMOTION_AMOUNT_KEYS:
        return VariableClassification("demotion", current_key, "Job demotion time")

    modifier_carriers = {
        "triggered_planet_modifier", "planet_modifier", "triggered_country_modifier", "country_modifier",
        "system_modifier", "triggered_planet_pop_group_modifier_for_all", "triggered_planet_pop_group_modifier_for_species",
    }
    if top in modifier_carriers:
        if category == "tpm":
            modifier_key = sibling_key if current_key in {"mult", "factor", "add"} and sibling_key else current_key
            return VariableClassification("tpm", modifier_key, f"Fallback mixed/special job modifier: {modifier_key}")
        modifier_key = sibling_key if current_key in {"mult", "factor", "add"} and sibling_key else current_key
        sem = semantic_category_for_modifier_key(modifier_key, top)
        if category in {"planet_state", "country_modifiers", "pop_modifiers", "economic_modifiers"}:
            domain = category
        elif sem in {"planet_state", "country_modifiers", "pop_modifiers", "economic_modifiers"}:
            domain = sem
        else:
            domain = "tpm"
        return VariableClassification(domain, modifier_key, f"Job modifier value: {modifier_key}")

    return None


class JobVariableAllocator:
    """Allocate object-specific job PIF variables."""

    def __init__(self, job_key: str, variables: Dict[str, str]):
        self.job_key = job_key
        self.source_variables = variables
        self.by_signature: Dict[Tuple[str, str, str], PifVariable] = {}
        self.counter_by_domain: Dict[str, int] = defaultdict(int)

    def resolve_scalar(self, atom: Atom) -> Optional[str]:
        if atom.quoted:
            return None
        if atom.value in {"yes", "no"}:
            return atom.value
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
                f"@pif_{sanitize_identifier(self.job_key)}_"
                f"{sanitize_identifier(classification.domain)}_{slug}_{self.counter_by_domain[classification.domain]}"
            )
            var = PifVariable(
                name=name,
                value=value,
                domain=classification.domain,
                job=self.job_key,
                purpose=classification.purpose,
            )
            self.by_signature[signature] = var
        var.uses.append(VariableUse(job=self.job_key, used_in=used_in, path=path))
        return Atom(var.name, quoted=False)

    def replace(self, node: Any, used_in: str, category: Optional[str] = None, path: Optional[List[str]] = None, sibling_key: Optional[str] = None) -> Any:
        """Replace meaningful job scalar/flag atoms with generated variables."""
        path = path or []
        if isinstance(node, Atom):
            value = self.resolve_scalar(node)
            if value is None:
                return clone_node(node)
            current_key = path[-1] if path else "value"
            cls = classify_variable_path(path, current_key, sibling_key, category, value)
            if cls is None:
                # Resolve vanilla @variables to literals for non-variableized contexts.
                return Atom(value, quoted=False) if node.value.startswith("@") and value not in {"yes", "no"} else clone_node(node)
            return self.allocate(value, cls, used_in, ".".join(path))
        if isinstance(node, Stmt):
            return Stmt(node.key, node.op, self.replace(node.value, used_in, category, path + [node.key], sibling_key))
        if isinstance(node, Block):
            sibling = sibling_modifier_key(node)
            return Block([self.replace(item, used_in, category, path, sibling) for item in node.items])
        return clone_node(node)

    def generated_variables(self) -> List[PifVariable]:
        return sorted(self.by_signature.values(), key=lambda v: (v.domain, v.job, v.name))


def variable_files_text(variables: List[PifVariable]) -> Dict[str, str]:
    """Render all job variable files grouped by job object."""
    by_domain: Dict[str, Dict[str, List[PifVariable]]] = defaultdict(lambda: defaultdict(list))
    for var in variables:
        by_domain[var.domain][var.job].append(var)

    rendered: Dict[str, str] = {}
    for domain, file_name in VARIABLE_DOMAIN_FILE_NAMES.items():
        lines = [
            "# Planetary Infrastructure Framework (PIF)",
            f"# Job variables: {VARIABLE_DOMAIN_TITLES[domain]}",
            "# Values are resolved from the Stellaris 4.3.7 vanilla pop_jobs baseline.",
            "# Variables are grouped by job object and are intentionally object-specific.",
            "",
        ]
        if domain not in by_domain:
            lines.append("# No variables were generated for this domain in the current vanilla baseline.")
        for job in sorted(by_domain.get(domain, {})):
            lines.append("# -----------------------------------------------------------------------------")
            lines.append(f"# {job}")
            lines.append("# -----------------------------------------------------------------------------")
            for var in sorted(by_domain[domain][job], key=lambda v: v.name):
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
