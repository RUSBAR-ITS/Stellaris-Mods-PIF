#!/usr/bin/env python3
"""
Generate the PIF Stage-5 pop job layer from vanilla Stellaris pop_jobs.

The generator expands vanilla inline scripts, splits job objects into PIF-owned
category inline scripts, normalizes accepted static modifier carriers and
replaces meaningful job tuning values with object-specific PIF scripted variables.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

from pif_stellaris import (
    Block,
    Stmt,
    add_common_args,
    ensure_clean_dir,
    load_project_from_args,
    make_inline_script_stmt,
    render_file,
    top_level_stmts,
    write_text,
)
from pif_backends.jobs_common import (
    CANONICAL_JOB_CATEGORIES,
    JobVariableAllocator,
    split_job_statement,
    variable_files_text,
    render_category_script,
    VARIABLE_DOMAIN_FILE_NAMES,
)


def pif_job_file_name(source_stem: str, job_key: str) -> str:
    """Return a stable generated file name for one pop job object."""
    return f"pif_{source_stem}_{job_key}.txt"


def bucket_job(expanded: Block) -> Tuple[Dict[str, List[Stmt]], List[str]]:
    """Split an expanded vanilla job body into PIF job categories."""
    buckets: Dict[str, List[Stmt]] = defaultdict(list)
    unknown: List[str] = []
    for stmt in top_level_stmts(expanded):
        for category, out_stmt in split_job_statement(stmt):
            if category == "unknown":
                unknown.append(out_stmt.key)
                category = "metadata"
            buckets[category].append(out_stmt)
    return buckets, unknown


def generate(project, out_root: Path, clean: bool = False, sparse_empty: bool = False) -> Dict[str, Any]:
    """Generate PIF job files, category scripts and variable files."""
    if clean:
        ensure_clean_dir(out_root)
    out_root.mkdir(parents=True, exist_ok=True)

    jobs = project.load_jobs()
    all_variables = []
    manifest_rows: List[Dict[str, Any]] = []
    class_counts = defaultdict(int)

    for job in jobs:
        class_counts[job.class_name] += 1
        local_vars = project.collect_local_variables(job.source_path)
        variables = {**project.global_variables, **local_vars}
        allocator = JobVariableAllocator(job.key, variables)

        buckets, unknown = bucket_job(job.expanded_body)
        job_file_rel = Path("common") / "pop_jobs" / pif_job_file_name(job.source_stem, job.key)
        job_file_abs = out_root / job_file_rel

        metadata_block = allocator.replace(Block(buckets.get("metadata", [])), job_file_rel.as_posix(), "metadata")
        root_items: List[Any] = list(metadata_block.items)
        generated_scripts: List[str] = []
        category_statement_counts: Dict[str, int] = {}

        for category in CANONICAL_JOB_CATEGORIES:
            category_items = buckets.get(category, [])
            category_statement_counts[category] = len(category_items)
            if sparse_empty and not category_items:
                continue
            script_path_no_ext = f"pif/jobs/{job.key}/{category}"
            root_items.append(make_inline_script_stmt(script_path_no_ext))
            category_rel = Path("common") / "inline_scripts" / "pif" / "jobs" / job.key / f"{category}.txt"
            category_abs = out_root / category_rel
            category_block = allocator.replace(Block(category_items), category_rel.as_posix(), category)
            header = (
                f"# PIF job category: {category.upper()}\n"
                f"# Vanilla job: {job.key}\n"
                f"# Vanilla class: {job.class_name}\n"
                f"# Vanilla source: {job.source_path.relative_to(project.root).as_posix()}\n\n"
            )
            write_text(category_abs, header + render_category_script(category_block.items, "Empty PIF job category hook."))
            generated_scripts.append(category_rel.as_posix())

        job_block = Block([Stmt(job.key, "=", Block(root_items))])
        header = (
            "# Planetary Infrastructure Framework (PIF)\n"
            f"# Generated from vanilla {job.source_path.relative_to(project.root).as_posix()}\n"
            f"# Object type: pop_job\n"
            f"# Job class: {job.class_name}\n\n"
        )
        write_text(job_file_abs, header + render_file(job_block))

        vars_for_job = allocator.generated_variables()
        all_variables.extend(vars_for_job)
        manifest_rows.append(
            {
                "job": job.key,
                "class": job.class_name,
                "vanilla_source": job.source_path.relative_to(project.root).as_posix(),
                "job_file": job_file_rel.as_posix(),
                "category_scripts": generated_scripts,
                "category_statement_counts": category_statement_counts,
                "metadata_statement_count": len(buckets.get("metadata", [])),
                "variables": [
                    {
                        "name": var.name,
                        "value": var.value,
                        "domain": var.domain,
                        "purpose": var.purpose,
                        "uses": [use.__dict__ for use in var.uses],
                    }
                    for var in vars_for_job
                ],
                "unknown_parameters": sorted(set(unknown)),
            }
        )

    for file_name, text in variable_files_text(all_variables).items():
        write_text(out_root / "common" / "scripted_variables" / file_name, text)

    domain_counts = defaultdict(int)
    for var in all_variables:
        domain_counts[var.domain] += 1

    manifest = {
        "profile": "jobs",
        "jobs": len(jobs),
        "classes": dict(sorted(class_counts.items())),
        "generated_object_files": len(manifest_rows),
        "generated_category_scripts": sum(len(row["category_scripts"]) for row in manifest_rows),
        "variables": len(all_variables),
        "variable_files": len(VARIABLE_DOMAIN_FILE_NAMES),
        "variable_domain_counts": dict(sorted(domain_counts.items())),
        "objects": manifest_rows,
    }
    manifest_path = out_root / "pif_job_generation_manifest.json"
    write_text(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    return {
        "profile": "jobs",
        "output": out_root.as_posix(),
        "jobs": len(jobs),
        "classes": dict(sorted(class_counts.items())),
        "generated_object_files": len(manifest_rows),
        "generated_category_scripts": sum(len(row["category_scripts"]) for row in manifest_rows),
        "variables": len(all_variables),
        "variable_files": len(VARIABLE_DOMAIN_FILE_NAMES),
        "variable_domain_counts": dict(sorted(domain_counts.items())),
        "manifest": manifest_path.as_posix(),
        "unknown_parameters": sorted({p for row in manifest_rows for p in row["unknown_parameters"]}),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    parser.add_argument("--out", default="/mnt/data/PIF_stage5_jobs", help="Generated PIF job output root")
    parser.add_argument("--clean", action="store_true", help="Delete output directory before generation")
    parser.add_argument("--sparse-empty", action="store_true", help="Skip empty category scripts")
    args = parser.parse_args()

    project = load_project_from_args(args)
    print(json.dumps(generate(project, Path(args.out), clean=args.clean, sparse_empty=args.sparse_empty), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
