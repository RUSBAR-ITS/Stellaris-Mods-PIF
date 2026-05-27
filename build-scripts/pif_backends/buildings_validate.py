#!/usr/bin/env python3
"""
Validate the generated PIF Stage-4 building layer against vanilla buildings.

The validator compares canonical expanded buckets rather than raw files.  This
allows accepted normalizations such as planet_modifier -> triggered_planet_modifier
while still detecting gameplay structure differences.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Set

from pif_stellaris import (
    Block,
    Stmt,
    add_common_args,
    load_project_from_args,
    replace_variables_for_compare,
    render_file,
    top_level_stmts,
    write_text,
)
from pif_backends.buildings_common import CANONICAL_BUILDING_CATEGORIES, split_building_statement


def _local_variable_map(project, obj) -> Dict[str, str]:
    return {**project.global_variables, **project.collect_local_variables(obj.source_path)}


def canonical_buckets(project, body: Block, variables: Dict[str, str]) -> Dict[str, str]:
    """Render canonical category buckets for comparison."""
    normalized = replace_variables_for_compare(body, variables)
    buckets: Dict[str, List[Stmt]] = defaultdict(list)
    for stmt in top_level_stmts(normalized):
        for category, out_stmt in split_building_statement(stmt):
            if category == "unknown":
                category = "metadata"
            buckets[category].append(out_stmt)
    order = ["metadata", *CANONICAL_BUILDING_CATEGORIES]
    return {category: render_file(Block(buckets.get(category, []))) for category in order}


def _building_refs_from_block(block: Block, keys: Set[str]) -> Set[str]:
    """Collect referenced building keys for simple reference validation."""
    refs: Set[str] = set()
    for stmt in top_level_stmts(block):
        if stmt.key in {"upgrades", "convert_to"} and isinstance(stmt.value, Block):
            for item in stmt.value.items:
                if hasattr(item, "value") and item.value in keys:
                    refs.add(item.value)
        if stmt.key in {"has_building", "has_building_construction"} and hasattr(stmt.value, "value"):
            if stmt.value.value in keys:
                refs.add(stmt.value.value)
    return refs


def _looks_like_job_specific_modifier(job_key: str, job_keys: Set[str]) -> bool:
    """Return True when a job_*_add key is a modifier on an existing job.

    Stellaris uses both job_<job>_add for job slots and keys such as
    job_healthcare_amenities_add for job-specific modifiers.  The latter must
    not be reported as missing job objects if a shorter prefix is a real job.
    """
    parts = job_key.split("_")
    for i in range(len(parts) - 1, 0, -1):
        if "_".join(parts[:i]) in job_keys:
            return True
    return False


def _job_modifier_warnings(vanilla_project) -> List[Dict[str, Any]]:
    """Warn about probable job-slot modifiers whose job object is absent."""
    job_keys = {key for key, _path, _body in vanilla_project.load_top_level_objects("pop_jobs")}
    warnings: List[Dict[str, Any]] = []
    missing: Dict[str, Set[str]] = defaultdict(set)
    for building in vanilla_project.load_buildings():
        for stmt in _iter_stmts(building.expanded_body):
            if not re.match(r"^job_.+_add$", stmt.key):
                continue
            job_key = stmt.key[len("job_") : -len("_add")]
            if job_key in job_keys or _looks_like_job_specific_modifier(job_key, job_keys):
                continue
            missing[stmt.key].add(building.key)
    for modifier, buildings in sorted(missing.items()):
        warnings.append({"type": "unresolved_probable_job_slot_modifier_ref", "modifier": modifier, "buildings": sorted(buildings)})
    return warnings


def _iter_stmts(block: Block):
    for item in block.items:
        if isinstance(item, Stmt):
            yield item
            if isinstance(item.value, Block):
                yield from _iter_stmts(item.value)
        elif isinstance(item, Block):
            yield from _iter_stmts(item)


def validate(vanilla_project, generated_project, out_path: Path) -> Dict[str, Any]:
    """Validate generated buildings and write a JSON report."""
    vanilla_objects = {obj.key: obj for obj in vanilla_project.load_buildings()}
    generated_objects = {obj.key: obj for obj in generated_project.load_buildings()}
    generated_vars = generated_project.global_variables

    rows: List[Dict[str, Any]] = []
    ok = 0
    failed = 0

    for key, vanilla in sorted(vanilla_objects.items()):
        generated = generated_objects.get(key)
        if generated is None:
            failed += 1
            rows.append({"building": key, "status": "FAIL", "reason": "missing generated building"})
            continue

        vanilla_canonical = canonical_buckets(vanilla_project, vanilla.expanded_body, _local_variable_map(vanilla_project, vanilla))
        generated_canonical = canonical_buckets(generated_project, generated.expanded_body, generated_vars)

        if vanilla_canonical == generated_canonical:
            ok += 1
            rows.append({"building": key, "status": "OK"})
            continue

        failed += 1
        differing = sorted(set(vanilla_canonical) | set(generated_canonical))
        differing = [category for category in differing if vanilla_canonical.get(category) != generated_canonical.get(category)]
        rows.append(
            {
                "building": key,
                "status": "FAIL",
                "reason": "canonical category mismatch",
                "differing_categories": differing,
                "vanilla": {category: vanilla_canonical.get(category, "") for category in differing},
                "generated": {category: generated_canonical.get(category, "") for category in differing},
            }
        )

    for key in sorted(set(generated_objects) - set(vanilla_objects)):
        failed += 1
        rows.append({"building": key, "status": "FAIL", "reason": "extra generated building"})

    warnings = _job_modifier_warnings(vanilla_project)
    report = {
        "profile": "buildings",
        "checked": len(vanilla_objects),
        "ok": ok,
        "failed": failed,
        "warnings": warnings,
        "rows": rows,
    }
    write_text(out_path, json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    return {"checked": len(vanilla_objects), "ok": ok, "failed": failed, "warnings": len(warnings), "report": out_path.as_posix()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    parser.add_argument("--generated", default="/mnt/data/PIF_stage4_buildings", help="Generated PIF building output root")
    parser.add_argument("--out", default="/mnt/data/PIF_stage4_buildings/pif_building_validation_report.json", help="Validation report JSON path")
    args = parser.parse_args()

    vanilla_project = load_project_from_args(args)
    from pif_stellaris import StellarisProject

    generated_project = StellarisProject(Path(args.generated))
    print(json.dumps(validate(vanilla_project, generated_project, Path(args.out)), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
