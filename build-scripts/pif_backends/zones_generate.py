#!/usr/bin/env python3
"""
Generate the PIF stage-2 zone layer from vanilla Stellaris zones.

Generated structure:

* one ``common/zones`` file per vanilla zone object;
* metadata stays in the zone object root;
* block/compatibility behavior is moved into per-zone category inline scripts;
* static zone modifiers are normalized to triggered equivalents;
* non-localization numeric scalars are moved into domain-specific scripted
  variable files whose names include ``zones``;
* ``swap_type_weight`` intentionally remains a literal by current PIF rule.

This script writes code, but it does not try to interpret game balance.  It only
performs deterministic structural transformation from the vanilla baseline.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pif_stellaris import (
    Atom,
    Block,
    Stmt,
    add_common_args,
    clone_node,
    ensure_clean_dir,
    load_project_from_args,
    make_inline_script_stmt,
    normalize_zone_modifier,
    render_file,
    resolve_atom_number,
    sanitize_identifier,
    top_level_stmts,
    write_text,
    zone_category_for_param,
    CANONICAL_ZONE_CATEGORIES,
)


# -----------------------------------------------------------------------------
# Variable-domain model for zones
# -----------------------------------------------------------------------------


DOMAIN_FILE_NAMES = {
    "construction": "pif_zones_construction_variables.txt",
    "economy": "pif_zones_economy_variables.txt",
    "housing": "pif_zones_housing_variables.txt",
    "building_capacity": "pif_zones_building_capacity_variables.txt",
    "planet_output_modifiers": "pif_zones_planet_output_modifiers_variables.txt",
    "ai": "pif_zones_ai_variables.txt",
    "zone_limits": "pif_zones_limits_variables.txt",
    "jobs_research": "pif_zones_jobs_research_variables.txt",
    "jobs_unity_admin": "pif_zones_jobs_unity_admin_variables.txt",
    "jobs_resource_extraction": "pif_zones_jobs_resource_extraction_variables.txt",
    "jobs_industry": "pif_zones_jobs_industry_variables.txt",
    "jobs_trade": "pif_zones_jobs_trade_variables.txt",
    "jobs_defense": "pif_zones_jobs_defense_variables.txt",
    "jobs_services": "pif_zones_jobs_services_variables.txt",
}

DOMAIN_TITLES = {
    "construction": "CONSTRUCTION",
    "economy": "ECONOMY",
    "housing": "HOUSING",
    "building_capacity": "BUILDING_CAPACITY",
    "planet_output_modifiers": "PLANET_OUTPUT_MODIFIERS",
    "ai": "AI",
    "zone_limits": "ZONE_LIMITS",
    "jobs_research": "JOBS_RESEARCH",
    "jobs_unity_admin": "JOBS_UNITY_ADMIN",
    "jobs_resource_extraction": "JOBS_RESOURCE_EXTRACTION",
    "jobs_industry": "JOBS_INDUSTRY",
    "jobs_trade": "JOBS_TRADE",
    "jobs_defense": "JOBS_DEFENSE",
    "jobs_services": "JOBS_SERVICES",
}

RESEARCH_JOB_MARKERS = ["researcher", "physicist", "physicists", "biologist", "biologists", "engineer", "engineers", "scientist", "archivist"]
UNITY_ADMIN_JOB_MARKERS = ["bureaucrat", "priest", "manager", "evaluator", "coordinator", "administrator", "unity", "culture_worker", "bio_trophy"]
RESOURCE_EXTRACTION_JOB_MARKERS = ["miner", "miners", "technician", "technicians", "farmer", "farmers", "agri", "gas", "crystal", "mote", "betharian", "mining_drone", "agri_drone", "wrangler", "acolyte_farm", "acolyte_generator"]
INDUSTRY_JOB_MARKERS = ["metallurgist", "artisan", "foundry", "factory", "fabricator", "catalytic", "chemist", "translucer", "gas_refiner"]
TRADE_JOB_MARKERS = ["clerk", "trader", "merchant", "trade"]
DEFENSE_JOB_MARKERS = ["soldier", "warrior", "duelist", "enforcer", "telepath", "defense", "battle_thrall", "knight"]
SERVICE_JOB_MARKERS = ["entertainer", "medical", "healthcare", "amenity", "maintenance", "servitor", "roboticist", "domestic", "logistics", "spawning_drone", "replicator"]


def job_family_from_key(key: str) -> str:
    """Map a job/modifier key to a zone job-family variable domain."""
    low = key.lower()
    for marker in RESEARCH_JOB_MARKERS:
        if marker in low:
            return "jobs_research"
    for marker in UNITY_ADMIN_JOB_MARKERS:
        if marker in low:
            return "jobs_unity_admin"
    for marker in RESOURCE_EXTRACTION_JOB_MARKERS:
        if marker in low:
            return "jobs_resource_extraction"
    for marker in INDUSTRY_JOB_MARKERS:
        if marker in low:
            return "jobs_industry"
    for marker in TRADE_JOB_MARKERS:
        if marker in low:
            return "jobs_trade"
    for marker in DEFENSE_JOB_MARKERS:
        if marker in low:
            return "jobs_defense"
    for marker in SERVICE_JOB_MARKERS:
        if marker in low:
            return "jobs_services"
    # Unknown jobs default to services because this domain is the least economy-
    # specific and is safer than incorrectly assigning research/industry output.
    return "jobs_services"


def sibling_modifier_key(block: Block) -> Optional[str]:
    """Return the first modifier-like sibling key in a block.

    This is used to classify numeric ``mult`` values in triggered district
    modifier blocks.  The number itself is attached to ``mult``, but the
    gameplay function is determined by the modifier that appears beside it.
    """
    for item in block.items:
        if not isinstance(item, Stmt):
            continue
        key = item.key
        if key == "mult" or key == "potential":
            continue
        if key.startswith("job_") or key.startswith("planet_"):
            return key
    return None


def variable_domain_for_scalar(path: List[str], current_key: str, sibling_key: Optional[str]) -> Optional[Tuple[str, str]]:
    """Return ``(domain, purpose)`` for a numeric scalar, or None to keep literal.

    The function classifies the scalar by gameplay function, not by PIF inline
    category.  Localization/tooltip selection and visual-swap weights are kept as
    literals by current project rules.
    """
    if "triggered_desc" in path:
        return None
    if current_key == "swap_type_weight" or "swap_type_weight" in path:
        return None

    path_text = ".".join(path + [current_key])

    if current_key == "base_buildtime":
        return "construction", "zone build time"
    if "resources" in path and "cost" in path:
        return "construction", f"zone construction cost: {current_key}"
    if "resources" in path and "upkeep" in path:
        return "economy", f"zone upkeep: {current_key}"
    if "resources" in path and "produces" in path:
        return "economy", f"zone direct production: {current_key}"

    if current_key in {"max_buildings", "districts_per_building"}:
        return "building_capacity", current_key
    if "planet_limit" in path or current_key == "planet_limit":
        return "zone_limits", path_text
    if current_key.startswith("ai_") or "ai_resource_production" in path or "ai_weight_coefficient" in path:
        return "ai", path_text

    modifier_key = sibling_key if current_key == "mult" and sibling_key else current_key
    if current_key == "mult" and sibling_key and sibling_key.startswith("job_"):
        return job_family_from_key(sibling_key), "district modifier scaling multiplier"
    if modifier_key.startswith("job_") and modifier_key.endswith("_add"):
        return job_family_from_key(modifier_key), f"job amount: {modifier_key}"

    if "housing" in modifier_key:
        return "housing", modifier_key
    if "max_buildings" in modifier_key or "building" in modifier_key and "slot" in modifier_key:
        return "building_capacity", modifier_key
    if "defense_armies" in modifier_key or "defensive_arm" in modifier_key:
        return "jobs_defense", modifier_key
    if modifier_key.startswith("planet_"):
        return "planet_output_modifiers", modifier_key

    return None


@dataclass
class VariableUse:
    """One place where a generated variable is used."""

    zone: str
    used_in: str
    path: str


@dataclass
class PifVariable:
    """A generated PIF scripted variable and all its usages."""

    name: str
    value: str
    domain: str
    zone: str
    purpose: str
    uses: List[VariableUse] = field(default_factory=list)


class ZoneVariableAllocator:
    """Allocate domain-specific, per-zone variables with local deduplication."""

    def __init__(self, zone_key: str, variables: Dict[str, str]):
        self.zone_key = zone_key
        self.source_variables = variables
        self.by_signature: Dict[Tuple[str, str, str], PifVariable] = {}
        self.counter_by_domain: Dict[str, int] = defaultdict(int)

    def resolve(self, atom: Atom) -> Optional[str]:
        return resolve_atom_number(atom, self.source_variables)

    def allocate(self, value: str, domain: str, purpose: str, used_in: str, path: str) -> Atom:
        signature = (domain, purpose, value)
        var = self.by_signature.get(signature)
        if var is None:
            self.counter_by_domain[domain] += 1
            slug = sanitize_identifier(purpose)
            if len(slug) > 72:
                slug = slug[:72].rstrip("_")
            name = f"@pif_{sanitize_identifier(self.zone_key)}_{sanitize_identifier(domain)}_{slug}_{self.counter_by_domain[domain]}"
            var = PifVariable(name=name, value=value, domain=domain, zone=self.zone_key, purpose=purpose)
            self.by_signature[signature] = var
        var.uses.append(VariableUse(zone=self.zone_key, used_in=used_in, path=path))
        return Atom(var.name, quoted=False)

    def replace(self, node: Any, used_in: str, path: Optional[List[str]] = None, sibling_key: Optional[str] = None) -> Any:
        """Replace numeric scalars in an AST node according to zone domain rules."""
        path = path or []
        if isinstance(node, Atom):
            value = self.resolve(node)
            if value is None:
                return clone_node(node)
            current_key = path[-1] if path else "value"
            domain = variable_domain_for_scalar(path[:-1], current_key, sibling_key)
            if domain is None:
                return clone_node(node)
            domain_name, purpose = domain
            return self.allocate(value, domain_name, purpose, used_in, ".".join(path))

        if isinstance(node, Stmt):
            new_path = path + [node.key]
            return Stmt(node.key, node.op, self.replace(node.value, used_in, new_path, sibling_key))

        if isinstance(node, Block):
            block_sibling_key = sibling_modifier_key(node)
            out: List[Any] = []
            counters: Dict[str, int] = defaultdict(int)
            for item in node.items:
                if isinstance(item, Stmt):
                    counters[item.key] += 1
                    # Keep repeated statement order visible in the path.  This
                    # helps comments and validation reports point to stable spots.
                    key_for_path = item.key if counters[item.key] == 1 else f"{item.key}_{counters[item.key]}"
                    out.append(self.replace(item, used_in, path + [key_for_path], block_sibling_key))
                else:
                    out.append(self.replace(item, used_in, path, block_sibling_key))
            return Block(out)

        return clone_node(node)

    def generated_variables(self) -> List[PifVariable]:
        return sorted(self.by_signature.values(), key=lambda v: (v.domain, v.zone, v.name))


# -----------------------------------------------------------------------------
# Zone generation
# -----------------------------------------------------------------------------


def pif_zone_file_name(source_stem: str, zone_key: str) -> str:
    return f"pif_{source_stem}_{zone_key}.txt"


def bucket_zone(expanded: Block) -> Tuple[Dict[str, List[Stmt]], List[str]]:
    """Split an expanded vanilla zone body into PIF zone categories."""
    buckets: Dict[str, List[Stmt]] = defaultdict(list)
    unknown: List[str] = []
    for stmt in top_level_stmts(expanded):
        transformed = normalize_zone_modifier(stmt)
        for out_stmt in transformed:
            category = zone_category_for_param(out_stmt.key)
            if category == "unknown":
                unknown.append(out_stmt.key)
                category = "metadata"
            buckets[category].append(out_stmt)
    return buckets, unknown


def variable_files_text(variables: List[PifVariable]) -> Dict[str, str]:
    """Render all domain variable files with zone-grouped sections."""
    by_domain: Dict[str, Dict[str, List[PifVariable]]] = defaultdict(lambda: defaultdict(list))
    for var in variables:
        by_domain[var.domain][var.zone].append(var)

    rendered: Dict[str, str] = {}
    for domain in DOMAIN_FILE_NAMES:
        lines = [
            f"# Planetary Infrastructure Framework (PIF)",
            f"# Zone variables: {DOMAIN_TITLES[domain]}",
            f"# Values are resolved from Stellaris 4.3.7 vanilla zones and inline scripts.",
            "",
        ]
        if domain not in by_domain:
            lines.append("# No variables were generated for this domain in the current vanilla baseline.")
        for zone in sorted(by_domain.get(domain, {})):
            lines.append(f"# -----------------------------------------------------------------------------")
            lines.append(f"# {zone}")
            lines.append(f"# -----------------------------------------------------------------------------")
            for var in sorted(by_domain[domain][zone], key=lambda v: v.name):
                uses = sorted({use.used_in for use in var.uses})
                lines.append(f"# Controls: {var.purpose}.")
                lines.append(f"# Used in: {', '.join(uses)}")
                lines.append(f"{var.name} = {var.value}")
                lines.append("")
        rendered[DOMAIN_FILE_NAMES[domain]] = "\n".join(lines).rstrip() + "\n"
    return rendered


def generate(project, out_root: Path, clean: bool = False, sparse_empty: bool = False) -> Dict[str, object]:
    """Generate PIF zone files, category inline scripts and variable files."""
    if clean:
        ensure_clean_dir(out_root)
    out_root.mkdir(parents=True, exist_ok=True)

    all_variables: List[PifVariable] = []
    manifest: List[Dict[str, object]] = []

    for zone in project.load_zones():
        local_vars = project.collect_local_variables(zone.source_path)
        variables = {**project.global_variables, **local_vars}
        allocator = ZoneVariableAllocator(zone.key, variables)

        buckets, unknown = bucket_zone(zone.expanded_body)
        zone_file_rel = Path("common") / "zones" / pif_zone_file_name(zone.source_stem, zone.key)
        zone_file_abs = out_root / zone_file_rel

        metadata = Block(buckets.get("metadata", []))
        metadata = allocator.replace(metadata, zone_file_rel.as_posix())
        root_items: List[Any] = list(metadata.items)
        generated_scripts: List[str] = []

        for category in CANONICAL_ZONE_CATEGORIES:
            category_items = buckets.get(category, [])
            if sparse_empty and not category_items:
                continue
            script_path_no_ext = f"pif/zones/{zone.key}/{category}"
            root_items.append(make_inline_script_stmt(script_path_no_ext))
            category_rel = Path("common") / "inline_scripts" / "pif" / "zones" / zone.key / f"{category}.txt"
            category_abs = out_root / category_rel
            category_block = allocator.replace(Block(category_items), category_rel.as_posix())
            header = (
                f"# PIF zone category: {category.upper()}\n"
                f"# Vanilla zone: {zone.key}\n"
                f"# Vanilla source: {zone.source_path.relative_to(project.root).as_posix()}\n\n"
            )
            write_text(category_abs, header + render_file(category_block))
            generated_scripts.append(category_rel.as_posix())

        zone_body = Block(root_items)
        zone_block = Block([Stmt(zone.key, "=", zone_body)])
        header = (
            "# Planetary Infrastructure Framework (PIF)\n"
            f"# Generated from vanilla {zone.source_path.relative_to(project.root).as_posix()}\n"
            "# Object type: zone\n\n"
        )
        write_text(zone_file_abs, header + render_file(zone_block))

        vars_for_zone = allocator.generated_variables()
        all_variables.extend(vars_for_zone)
        manifest.append(
            {
                "zone": zone.key,
                "vanilla_source": zone.source_path.relative_to(project.root).as_posix(),
                "zone_file": zone_file_rel.as_posix(),
                "category_scripts": generated_scripts,
                "variables": [
                    {
                        "name": var.name,
                        "value": var.value,
                        "domain": var.domain,
                        "purpose": var.purpose,
                        "uses": [use.__dict__ for use in var.uses],
                    }
                    for var in vars_for_zone
                ],
                "unknown_parameters": sorted(set(unknown)),
            }
        )

    for file_name, text in variable_files_text(all_variables).items():
        write_text(out_root / "common" / "scripted_variables" / file_name, text)

    manifest_path = out_root / "pif_zone_generation_manifest.json"
    write_text(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    return {
        "zones": len(manifest),
        "category_scripts": sum(len(row["category_scripts"]) for row in manifest),
        "variables": len(all_variables),
        "variable_files": len(DOMAIN_FILE_NAMES),
        "manifest": manifest_path.as_posix(),
        "unknown_parameters": sorted({p for row in manifest for p in row["unknown_parameters"]}),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    parser.add_argument("--out", default="/mnt/data/PIF_stage2_zones", help="PIF output root")
    parser.add_argument("--clean", action="store_true", help="Delete output directory before generation")
    parser.add_argument("--sparse-empty", action="store_true", help="Do not create empty category inline scripts")
    args = parser.parse_args()

    project = load_project_from_args(args)
    print(json.dumps(generate(project, Path(args.out), clean=args.clean, sparse_empty=args.sparse_empty), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
