#!/usr/bin/env python3
"""
Generate the first PIF district layer from vanilla Stellaris 4.3.7 districts.

This generator produces the actual mod-facing district layer used by
Planetary Infrastructure Framework (PIF).  It is intentionally conservative:
all gameplay objects are generated from expanded vanilla district definitions,
then reshaped into PIF's compatibility structure without changing their static
meaning.

Generated structure:
- one common/districts file per vanilla district object;
- real districts use category inline scripts: zone_slots, availability,
  economic, tpm, lifecycle, ai;
- district masks stay compact: METADATA + MASK only;
- vanilla planet_modifier blocks are normalized into triggered_planet_modifier
  blocks with always=yes because triggered_planet_modifier is append-friendly;
- numeric scalar values are moved to domain-based scripted_variables files,
  not to per-object files and not to inline-category files;
- localization blocks are deliberately excluded from scalar extraction because
  localization is already externalized through localization keys and can be
  changed by separate localization mods.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from pif_stellaris import (
    Atom,
    Block,
    Stmt,
    add_common_args,
    category_for_param,
    clone_node,
    ensure_clean_dir,
    is_numeric_literal,
    load_project_from_args,
    make_inline_script_stmt,
    normalize_planet_modifier,
    render_file,
    sanitize_identifier,
    top_level_stmts,
    write_text,
    CANONICAL_REAL_CATEGORIES,
)


# -----------------------------------------------------------------------------
# Variable-domain model
# -----------------------------------------------------------------------------

# Top-level localization fields are not gameplay tuning values for PIF variable
# extraction.  Numeric values inside their triggers (for example num_zones
# value > 0) are selector thresholds for localization strings, not reusable
# district balance constants.
LOCALIZATION_TOP_KEYS = {"desc", "triggered_desc", "triggered_name", "triggered_flavor_desc"}


@dataclass(frozen=True)
class VariableDomain:
    """Metadata for one PIF scripted-variable file/domain.

    The domain key is intentionally independent from inline-script categories.
    Inline categories answer "where is this block stored?"; variable domains
    answer "what does this number control in gameplay?".
    """

    key: str
    display: str
    file_name: str
    description: str


VARIABLE_DOMAINS: Dict[str, VariableDomain] = {
    "construction": VariableDomain(
        "construction",
        "CONSTRUCTION",
        "pif_districts_construction_variables.txt",
        "District purchase/build costs and district construction time.",
    ),
    "economy": VariableDomain(
        "economy",
        "ECONOMY",
        "pif_districts_economy_variables.txt",
        "District upkeep and direct resource production.",
    ),
    "jobs": VariableDomain(
        "jobs",
        "JOBS",
        "pif_districts_jobs_variables.txt",
        "Job counts added by district modifiers.",
    ),
    "housing": VariableDomain(
        "housing",
        "HOUSING",
        "pif_districts_housing_variables.txt",
        "Housing capacity provided by districts.",
    ),
    "building_capacity": VariableDomain(
        "building_capacity",
        "BUILDING_CAPACITY",
        "pif_districts_building_capacity_variables.txt",
        "Building capacity / max-building modifiers provided by districts.",
    ),
    "infrastructure_effects": VariableDomain(
        "infrastructure_effects",
        "INFRASTRUCTURE_EFFECTS",
        "pif_districts_infrastructure_effects_variables.txt",
        "Infrastructure-related speed modifiers provided by districts.",
    ),
    "defense": VariableDomain(
        "defense",
        "DEFENSE",
        "pif_districts_defense_variables.txt",
        "Defensive armies or similar defensive values provided by districts.",
    ),
    "ai": VariableDomain(
        "ai",
        "AI",
        "pif_districts_ai_variables.txt",
        "AI planning hints and AI weighting constants for districts.",
    ),
    "limits": VariableDomain(
        "limits",
        "DISTRICT_LIMITS",
        "pif_districts_limits_variables.txt",
        "Deposit/feature based district cap-generation values.",
    ),
    "conversion": VariableDomain(
        "conversion",
        "CONVERSION",
        "pif_districts_conversion_variables.txt",
        "District conversion ratios used when districts convert to another type.",
    ),
}

VARIABLE_DOMAIN_ORDER = [
    "construction",
    "economy",
    "jobs",
    "housing",
    "building_capacity",
    "infrastructure_effects",
    "defense",
    "ai",
    "limits",
    "conversion",
]


@dataclass(frozen=True)
class VariableClassification:
    """Semantic classification of one numeric scalar occurrence."""

    domain: str
    function_key: str
    purpose: str


def _resource_from_path(path: List[str], index: int) -> str:
    """Return a resource key from a parsed AST path, defensively."""
    return path[index] if len(path) > index else "resource"


def classify_variable_path(path: List[str]) -> VariableClassification | None:
    """Classify a numeric scalar by gameplay purpose.

    The classifier uses actual AST context rather than the original vanilla
    variable name.  This is important because vanilla uses short local names
    like @base_cost in several files with different values and different roles.

    Returning None means "do not replace this scalar".  This is currently used
    for localization-selector thresholds and for any unexpected scalar that we
    decide not to variableize until it has been manually reviewed.
    """

    if not path:
        return None

    top = path[0]
    leaf = path[-1]

    # Localization is externalized through localization keys.  The numeric
    # thresholds inside triggered localization blocks select strings; they are
    # not PIF tuning variables.
    if top in LOCALIZATION_TOP_KEYS:
        return None

    # District construction/purchase values.
    if top == "base_buildtime":
        return VariableClassification("construction", "build_time_days", "District construction time in days")
    if len(path) >= 3 and path[0] == "resources" and path[1] == "cost":
        res = _resource_from_path(path, 2)
        return VariableClassification("construction", f"build_cost_{res}", f"District build/purchase cost in {res}")

    # District direct economy: upkeep and direct production.  Jobs and housing
    # are intentionally kept out of this domain because modders often rebalance
    # them independently from resource upkeep.
    if len(path) >= 3 and path[0] == "resources" and path[1] == "upkeep":
        res = _resource_from_path(path, 2)
        return VariableClassification("economy", f"district_upkeep_{res}", f"District resource upkeep in {res}")
    if len(path) >= 3 and path[0] == "resources" and path[1] == "produces":
        res = _resource_from_path(path, 2)
        return VariableClassification("economy", f"district_produces_{res}", f"District direct resource production in {res}")
    if leaf.startswith("planet_neural_chips_") and leaf.endswith("_produces_add"):
        res = leaf.removeprefix("planet_neural_chips_").removesuffix("_produces_add")
        return VariableClassification("economy", f"planet_neural_chips_produces_{res}", f"Planetary neural chips flat production in {res}")

    # Job counts are gameplay output, not general planet modifiers.
    if re.match(r"^job_.+_add$", leaf):
        job = leaf[len("job_") : -len("_add")]
        return VariableClassification("jobs", f"job_{job}_add", f"Number of {job} jobs added by the district")

    # Housing is large enough and important enough to deserve its own domain.
    if leaf == "planet_housing_add":
        return VariableClassification("housing", "planet_housing_add", "Planet housing added by the district")

    # Building capacity / max building values.
    if leaf.endswith("_max_buildings_add") or leaf == "planet_max_buildings_add":
        return VariableClassification("building_capacity", leaf, "Additional building capacity unlocked by the district")

    # District-provided speed effects that change broader planetary
    # infrastructure behavior.
    if leaf in {"planet_building_build_speed_mult", "planet_decision_enact_speed_mult"}:
        return VariableClassification("infrastructure_effects", leaf, "Planet infrastructure/decision speed modifier provided by the district")

    # Defensive outputs.
    if leaf == "planet_defense_armies_add":
        return VariableClassification("defense", leaf, "Defense armies added by the district")

    # AI values do not directly change player-visible output, but they are a
    # compatibility surface for AI/economy mods.
    if top == "ai_resource_production":
        return VariableClassification("ai", f"ai_resource_production_{leaf}", f"AI planning hint for {leaf} production")
    if top in {"ai_weight_coefficient", "additional_ai_weight", "ai_estimate_without_unemployment"}:
        return VariableClassification("ai", top, "AI district planning weight/tuning value")

    # District cap generation based on deposits/features.
    if top in {"min_for_deposits_on_planet", "max_for_deposits_on_planet"}:
        return VariableClassification("limits", top, "Deposit-based district cap generation value")

    # Lifecycle conversion ratio.  It is a technical behavior value, but we keep
    # it in a separate domain because the project decided to expose it explicitly.
    if top == "conversion_ratio":
        return VariableClassification("conversion", "conversion_ratio", "District conversion ratio used during district type conversion")

    # Unknown numeric scalars should remain literal until we consciously decide
    # what they mean.  This avoids creating misleading variables.
    return None


# -----------------------------------------------------------------------------
# Variable allocation
# -----------------------------------------------------------------------------


@dataclass
class PifVariable:
    """One generated PIF scripted variable."""

    name: str
    value: str
    district: str
    domain: str
    function_key: str
    purpose: str
    used_in: set[str] = field(default_factory=set)
    paths: set[str] = field(default_factory=set)
    vanilla_variables: set[str] = field(default_factory=set)

    def to_manifest(self) -> Dict[str, Any]:
        """Convert the variable to a JSON-serializable manifest row."""
        return {
            "name": self.name,
            "value": self.value,
            "district": self.district,
            "domain": self.domain,
            "function_key": self.function_key,
            "purpose": self.purpose,
            "used_in": sorted(self.used_in),
            "paths": sorted(self.paths),
            "vanilla_variables": sorted(self.vanilla_variables),
        }


class VariableRegistry:
    """Global registry for all generated PIF district variables.

    Variables are grouped by semantic domain and by district in the output
    files.  Dedupe happens only inside one district + one domain + one function
    + one resolved value.  That means a vanilla shared variable like
    @base_district_jobs is deliberately split into district-specific PIF
    variables, while repeated occurrences of the same function inside the same
    district can reuse one variable.
    """

    def __init__(self) -> None:
        self.by_key: Dict[Tuple[str, str, str, str], PifVariable] = {}
        self.used_names: set[str] = set()

    def _make_unique_name(self, district: str, domain: str, function_key: str) -> str:
        base = f"@pif_{sanitize_identifier(district)}_{sanitize_identifier(domain)}_{sanitize_identifier(function_key)}"
        name = base
        i = 2
        while name in self.used_names:
            name = f"{base}_{i}"
            i += 1
        self.used_names.add(name)
        return name

    def get_or_create(
        self,
        *,
        district: str,
        classification: VariableClassification,
        value: str,
        used_in: str,
        path: List[str],
        vanilla_variable: str | None,
    ) -> PifVariable:
        key = (district, classification.domain, classification.function_key, value)
        if key not in self.by_key:
            self.by_key[key] = PifVariable(
                name=self._make_unique_name(district, classification.domain, classification.function_key),
                value=value,
                district=district,
                domain=classification.domain,
                function_key=classification.function_key,
                purpose=classification.purpose,
            )
        var = self.by_key[key]
        var.used_in.add(used_in)
        var.paths.add(".".join(path))
        if vanilla_variable:
            var.vanilla_variables.add(vanilla_variable)
        return var

    def variables(self) -> List[PifVariable]:
        return list(self.by_key.values())

    def variables_by_domain(self) -> Dict[str, List[PifVariable]]:
        out: Dict[str, List[PifVariable]] = defaultdict(list)
        for var in self.variables():
            out[var.domain].append(var)
        return out


class ScalarReplacer:
    """Replace eligible numeric atoms with PIF variables.

    Each district has its own replacer because vanilla local variables are scoped
    to one source file.  The replacer resolves vanilla @variables to concrete
    numbers before writing PIF variables, so generated variables never point at
    other variables.
    """

    def __init__(self, district_key: str, var_values: Dict[str, str], registry: VariableRegistry) -> None:
        self.district_key = district_key
        self.var_values = var_values
        self.registry = registry
        self.replaced_count = 0
        self.unclassified_numeric: List[Dict[str, str]] = []

    def resolve_numeric(self, atom: Atom) -> Tuple[str | None, str | None]:
        """Return (literal_number, vanilla_variable_name) for a numeric atom."""
        value = atom.value
        if atom.quoted:
            return None, None
        if is_numeric_literal(value):
            return value, None
        if value.startswith("@") and value in self.var_values and is_numeric_literal(self.var_values[value]):
            return self.var_values[value], value
        return None, None

    def replace(self, node: Any, used_in: str, path: List[str] | None = None) -> Any:
        """Recursively replace eligible scalar values in an AST node."""
        path = path or []
        if isinstance(node, Atom):
            literal, vanilla_variable = self.resolve_numeric(node)
            if literal is None:
                return clone_node(node)
            classification = classify_variable_path(path)
            if classification is None:
                # Keep localization thresholds and unknown scalars literal.
                if path and path[0] not in LOCALIZATION_TOP_KEYS:
                    self.unclassified_numeric.append({"path": ".".join(path), "value": literal})
                return clone_node(node)
            var = self.registry.get_or_create(
                district=self.district_key,
                classification=classification,
                value=literal,
                used_in=used_in,
                path=path,
                vanilla_variable=vanilla_variable,
            )
            self.replaced_count += 1
            return Atom(var.name, quoted=False)
        if isinstance(node, Stmt):
            return Stmt(node.key, node.op, self.replace(node.value, used_in, path + [node.key]))
        if isinstance(node, Block):
            return Block([self.replace(item, used_in, path) for item in node.items])
        return clone_node(node)


# -----------------------------------------------------------------------------
# Output helpers
# -----------------------------------------------------------------------------


def render_variable_file(domain_key: str, variables: List[PifVariable]) -> str:
    """Render one domain-based scripted_variables file."""
    domain = VARIABLE_DOMAINS[domain_key]
    lines: List[str] = [
        "# Planetary Infrastructure Framework (PIF)",
        f"# Variable domain: {domain.display}",
        f"# {domain.description}",
        "#",
        "# Values in this file are generated from vanilla Stellaris 4.3.7 districts.",
        "# They are grouped by district. Vanilla shared variables are resolved to",
        "# concrete numbers and split per district/function; PIF variables do not",
        "# point to other variables.",
        "",
    ]

    by_district: Dict[str, List[PifVariable]] = defaultdict(list)
    for var in variables:
        by_district[var.district].append(var)

    for district in sorted(by_district):
        lines.append(f"# -----------------------------------------------------------------------------")
        lines.append(f"# {district}")
        lines.append(f"# -----------------------------------------------------------------------------")
        for var in sorted(by_district[district], key=lambda v: (v.function_key, numeric_sort_key(v.value), v.name)):
            lines.append(f"# Controls: {var.purpose}.")
            lines.append(f"# District: {var.district}")
            lines.append(f"# Used by: {', '.join(sorted(var.used_in))}")
            lines.append(f"# Contexts: {' | '.join(sorted(var.paths))}")
            if var.vanilla_variables:
                lines.append(f"# Resolved vanilla variable(s): {', '.join(sorted(var.vanilla_variables))}")
            lines.append(f"{var.name} = {var.value}")
            lines.append("")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def numeric_sort_key(value: str) -> Tuple[int, float | str]:
    """Sort numeric-looking values numerically and fall back to string order."""
    try:
        return (0, float(value))
    except ValueError:
        return (1, value)


def pif_district_file_name(source_stem: str, district_key: str) -> str:
    return f"pif_{source_stem}_{district_key}.txt"


def bucket_real_district(expanded: Block) -> Tuple[Dict[str, List[Stmt]], List[str]]:
    """Split an expanded real district into PIF inline-script categories."""
    buckets: Dict[str, List[Stmt]] = defaultdict(list)
    unknown: List[str] = []
    for stmt in top_level_stmts(expanded):
        transformed = normalize_planet_modifier(stmt)
        for out_stmt in transformed:
            cat = category_for_param(out_stmt.key, district_class="real")
            if cat == "unknown":
                unknown.append(out_stmt.key)
                cat = "metadata"
            buckets[cat].append(out_stmt)
    return buckets, unknown


def bucket_mask(expanded: Block) -> Tuple[List[Stmt], List[str]]:
    """Return the compact METADATA + MASK sequence for a district mask."""
    items: List[Stmt] = []
    unknown: List[str] = []
    for stmt in top_level_stmts(expanded):
        cat = category_for_param(stmt.key, district_class="active_mask")
        if cat == "unknown":
            unknown.append(stmt.key)
        else:
            items.append(stmt)
    return items, unknown


# -----------------------------------------------------------------------------
# Generation
# -----------------------------------------------------------------------------


def generate(project, out_root: Path, clean: bool = False) -> Dict[str, Any]:
    """Generate PIF district files, category scripts and domain variable files."""
    if clean:
        ensure_clean_dir(out_root)
    out_root.mkdir(parents=True, exist_ok=True)

    registry = VariableRegistry()
    manifest = []
    all_unclassified_numeric: List[Dict[str, str]] = []

    for district in project.load_districts():
        local_vars = project.collect_local_variables(district.source_path)
        var_values = {**project.global_variables, **local_vars}
        replacer = ScalarReplacer(district.key, var_values, registry)

        district_file_rel = Path("common") / "districts" / pif_district_file_name(district.source_stem, district.key)
        district_file_abs = out_root / district_file_rel

        unknown: List[str] = []
        generated_scripts: List[str] = []

        if district.class_name == "real":
            buckets, unknown = bucket_real_district(district.expanded_body)

            # Root metadata stays in the district object.  Eligible numeric values
            # inside metadata (for example build time or deposit cap values) still
            # move to domain variable files.
            metadata = Block(buckets.get("metadata", []))
            metadata = replacer.replace(metadata, district_file_rel.as_posix())

            root_items: List[Any] = list(metadata.items)
            for category in CANONICAL_REAL_CATEGORIES:
                script_path_no_ext = f"pif/districts/{district.key}/{category}"
                root_items.append(make_inline_script_stmt(script_path_no_ext))

                category_rel = Path("common") / "inline_scripts" / "pif" / "districts" / district.key / f"{category}.txt"
                category_abs = out_root / category_rel
                category_block = Block(buckets.get(category, []))
                category_block = replacer.replace(category_block, category_rel.as_posix())
                header = (
                    f"# PIF category: {category.upper()}\n"
                    f"# Vanilla district: {district.key}\n"
                    f"# Vanilla source: {district.source_path.relative_to(project.root).as_posix()}\n\n"
                )
                write_text(category_abs, header + render_file(category_block))
                generated_scripts.append(category_rel.as_posix())

            district_body = Block(root_items)
        else:
            # District masks are not real districts.  They remain compact and
            # only keep METADATA + MASK fields.  Localization-selector thresholds
            # inside mask names/descriptions are intentionally not variableized.
            mask_items, unknown = bucket_mask(district.expanded_body)
            mask_block = Block(mask_items)
            mask_block = replacer.replace(mask_block, district_file_rel.as_posix())
            district_body = mask_block

        for row in replacer.unclassified_numeric:
            all_unclassified_numeric.append({"district": district.key, **row})

        district_block = Block([Stmt(district.key, "=", district_body)])
        header = (
            f"# Planetary Infrastructure Framework (PIF)\n"
            f"# Generated from vanilla {district.source_path.relative_to(project.root).as_posix()}\n"
            f"# Object class: {district.class_name}\n\n"
        )
        write_text(district_file_abs, header + render_file(district_block))

        manifest.append(
            {
                "district": district.key,
                "class": district.class_name,
                "vanilla_source": district.source_path.relative_to(project.root).as_posix(),
                "district_file": district_file_rel.as_posix(),
                "category_scripts": generated_scripts,
                "unknown_parameters": sorted(set(unknown)),
                "replaced_numeric_scalars": replacer.replaced_count,
                "unclassified_numeric_scalars": replacer.unclassified_numeric,
            }
        )

    # Domain variable files are written after all districts have been processed.
    variables_by_domain = registry.variables_by_domain()
    variable_files: Dict[str, str] = {}
    for domain_key in VARIABLE_DOMAIN_ORDER:
        domain = VARIABLE_DOMAINS[domain_key]
        vars_for_domain = variables_by_domain.get(domain_key, [])
        variable_rel = Path("common") / "scripted_variables" / domain.file_name
        variable_abs = out_root / variable_rel
        write_text(variable_abs, render_variable_file(domain_key, vars_for_domain))
        variable_files[domain_key] = variable_rel.as_posix()

    variables = registry.variables()
    manifest_path = out_root / "pif_district_generation_manifest.json"
    write_text(
        manifest_path,
        json.dumps(
            {
                "districts": manifest,
                "variables": [var.to_manifest() for var in sorted(variables, key=lambda v: (v.domain, v.district, v.function_key, numeric_sort_key(v.value), v.name))],
                "variable_files": variable_files,
                "unclassified_numeric_scalars": all_unclassified_numeric,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
    )

    return {
        "districts": len(manifest),
        "real": sum(1 for x in manifest if x["class"] == "real"),
        "active_masks": sum(1 for x in manifest if x["class"] == "active_mask"),
        "sleeping_masks": sum(1 for x in manifest if x["class"] == "sleeping_mask"),
        "variables": len(variables),
        "variable_files": len(variable_files),
        "unclassified_numeric_scalars": len(all_unclassified_numeric),
        "manifest": manifest_path.as_posix(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    parser.add_argument("--out", default="/mnt/data/PIF_stage1", help="PIF output root")
    parser.add_argument("--clean", action="store_true", help="Delete output directory before generation")
    args = parser.parse_args()

    project = load_project_from_args(args)
    summary = generate(project, Path(args.out), clean=args.clean)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
