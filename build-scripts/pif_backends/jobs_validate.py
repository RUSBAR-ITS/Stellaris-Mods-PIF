#!/usr/bin/env python3
"""
Validate the generated PIF Stage-5 pop job layer against vanilla pop_jobs.

The validator compares canonical expanded buckets rather than raw files.  This
allows accepted normalizations such as planet_modifier -> triggered_planet_modifier
and object-specific PIF variables while detecting gameplay-structure differences.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from pif_stellaris import (
    Atom,
    Block,
    Stmt,
    add_common_args,
    load_project_from_args,
    render_file,
    top_level_stmts,
    write_text,
)
from pif_backends.jobs_common import CANONICAL_JOB_CATEGORIES, split_job_statement


def _local_variable_map(project, obj) -> Dict[str, str]:
    return {**project.global_variables, **project.collect_local_variables(obj.source_path)}


def _replace_variables_for_compare_all(node: Any, variables: Dict[str, str]) -> Any:
    """Replace numeric and yes/no variable references for Stage-5 comparison."""
    from pif_stellaris import is_numeric_literal

    if isinstance(node, Atom):
        if not node.quoted and node.value.startswith("@") and node.value in variables:
            value = variables[node.value]
            if is_numeric_literal(value) or value in {"yes", "no"}:
                return Atom(value, quoted=False)
        return Atom(node.value, node.quoted)
    if isinstance(node, Stmt):
        return Stmt(node.key, node.op, _replace_variables_for_compare_all(node.value, variables))
    if isinstance(node, Block):
        return Block([_replace_variables_for_compare_all(item, variables) for item in node.items])
    return node


def canonical_buckets(body: Block, variables: Dict[str, str]) -> Dict[str, str]:
    """Render canonical category buckets for comparison."""
    normalized = _replace_variables_for_compare_all(body, variables)
    buckets: Dict[str, List[Stmt]] = {"metadata": []}
    for category in CANONICAL_JOB_CATEGORIES:
        buckets[category] = []
    for stmt in top_level_stmts(normalized):
        for category, out_stmt in split_job_statement(stmt):
            if category == "unknown":
                category = "metadata"
            buckets.setdefault(category, []).append(out_stmt)
    order = ["metadata", *CANONICAL_JOB_CATEGORIES]
    return {category: render_file(Block(buckets.get(category, []))) for category in order}


def validate(vanilla_project, generated_project, out_path: Path) -> Dict[str, Any]:
    """Validate generated jobs and write a JSON report."""
    vanilla_objects = {obj.key: obj for obj in vanilla_project.load_jobs()}
    generated_objects = {obj.key: obj for obj in generated_project.load_jobs()}
    generated_vars = generated_project.global_variables

    rows: List[Dict[str, Any]] = []
    ok = 0
    failed = 0

    for key, vanilla in sorted(vanilla_objects.items()):
        generated = generated_objects.get(key)
        if generated is None:
            failed += 1
            rows.append({"job": key, "status": "FAIL", "reason": "missing generated job"})
            continue

        vanilla_canonical = canonical_buckets(vanilla.expanded_body, _local_variable_map(vanilla_project, vanilla))
        generated_canonical = canonical_buckets(generated.expanded_body, generated_vars)

        if vanilla_canonical == generated_canonical:
            ok += 1
            rows.append({"job": key, "status": "OK"})
            continue

        failed += 1
        differing = sorted(set(vanilla_canonical) | set(generated_canonical))
        differing = [category for category in differing if vanilla_canonical.get(category) != generated_canonical.get(category)]
        rows.append(
            {
                "job": key,
                "status": "FAIL",
                "reason": "canonical category mismatch",
                "differing_categories": differing,
                "vanilla": {category: vanilla_canonical.get(category, "") for category in differing},
                "generated": {category: generated_canonical.get(category, "") for category in differing},
            }
        )

    for key in sorted(set(generated_objects) - set(vanilla_objects)):
        failed += 1
        rows.append({"job": key, "status": "FAIL", "reason": "extra generated job"})

    report = {
        "profile": "jobs",
        "checked": len(vanilla_objects),
        "ok": ok,
        "failed": failed,
        "warnings": [],
        "rows": rows,
    }
    write_text(out_path, json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    return {"checked": len(vanilla_objects), "ok": ok, "failed": failed, "warnings": 0, "report": out_path.as_posix()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    parser.add_argument("--generated", default="/mnt/data/PIF_stage5_jobs", help="Generated PIF job output root")
    parser.add_argument("--out", default="/mnt/data/PIF_stage5_jobs/pif_job_validation_report.json", help="Validation report JSON path")
    args = parser.parse_args()

    vanilla_project = load_project_from_args(args)
    from pif_stellaris import StellarisProject

    generated_project = StellarisProject(Path(args.generated))
    print(json.dumps(validate(vanilla_project, generated_project, Path(args.out)), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
