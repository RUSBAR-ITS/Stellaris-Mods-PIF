#!/usr/bin/env python3
"""
Profile-driven analysis command for PIF object families.

The command expands vanilla inline scripts recursively and reports top-level
parameters, source files and reachable inline scripts for the selected profile.
It is intentionally generic: adding a new object type should require a new
profile/backend, not a cloned analyzer.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List

from pif_profiles import get_profile, list_profiles
from pif_stellaris import (
    Block,
    Stmt,
    add_common_args,
    load_project_from_args,
    top_level_stmts,
    write_text,
)


def load_objects(project, profile):
    """Load expanded objects for the selected profile."""
    if profile.name == "districts":
        return project.load_districts()
    if profile.name == "zones":
        return project.load_zones()
    if profile.name == "zone_slots":
        return project.load_zone_slots()
    if profile.name == "buildings":
        return project.load_buildings()
    if profile.name == "jobs":
        return project.load_jobs()
    raise NotImplementedError(profile.name)


def object_class(obj) -> str:
    """Return the profile-specific class label for reporting."""
    return getattr(obj, "class_name", "zone_slot" if obj.key.startswith("slot_") else "zone")


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    """Write a UTF-8 CSV file with stable columns."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def analyze(profile_name: str, out_dir: Path, planet: str, work_dir: str | None = None) -> Dict[str, Any]:
    """Run profile analysis and write CSV/JSON reports."""
    profile = get_profile(profile_name)

    class Args:
        pass

    args = Args()
    args.planet = planet
    args.work_dir = work_dir
    project = load_project_from_args(args)
    objects = load_objects(project, profile)
    out_dir.mkdir(parents=True, exist_ok=True)

    param_counts: Counter[str] = Counter()
    param_by_class: Dict[str, Counter[str]] = defaultdict(Counter)
    param_by_file: Dict[str, Counter[str]] = defaultdict(Counter)
    object_rows: List[Dict[str, Any]] = []
    reachable: Dict[str, Counter[str]] = defaultdict(Counter)

    for obj in objects:
        cls = object_class(obj)
        rel_source = obj.source_path.relative_to(project.root).as_posix()
        params = []
        for stmt in top_level_stmts(obj.expanded_body):
            params.append(stmt.key)
        unique_params = sorted(set(params))
        for key in unique_params:
            param_counts[key] += 1
            param_by_class[cls][key] += 1
            param_by_file[rel_source][key] += 1
        for script in project.reachable_inline_scripts_from_block(obj.body):
            reachable[script][obj.key] += 1
        object_rows.append(
            {
                "object": obj.key,
                "class": cls,
                "source_file": rel_source,
                "source_stem": obj.source_stem,
                "top_level_params_after_expansion": " ".join(unique_params),
            }
        )

    param_rows: List[Dict[str, Any]] = []
    all_classes = sorted(param_by_class)
    for key in sorted(param_counts):
        row: Dict[str, Any] = {
            "parameter": key,
            "sum_objects": param_counts[key],
            "category": profile.category_for_param(
                key,
                object_class="real" if profile.name == "districts" else ("regular" if profile.name == "buildings" else ("worker" if profile.name == "jobs" else "zone")),
            ),
        }
        for cls in all_classes:
            row[f"class_{cls}"] = param_by_class[cls][key]
        param_rows.append(row)

    script_rows = [
        {
            "inline_script": script,
            "object_count": len(obj_counts),
            "call_count": sum(obj_counts.values()),
            "objects": " ".join(sorted(obj_counts)),
        }
        for script, obj_counts in sorted(reachable.items())
    ]

    write_csv(out_dir / f"{profile.name}_objects.csv", object_rows, ["object", "class", "source_file", "source_stem", "top_level_params_after_expansion"])
    param_fields = ["parameter", "sum_objects", "category"] + [f"class_{cls}" for cls in all_classes]
    write_csv(out_dir / f"{profile.name}_parameters_after_expansion.csv", param_rows, param_fields)
    write_csv(out_dir / f"{profile.name}_reachable_inline_scripts.csv", script_rows, ["inline_script", "object_count", "call_count", "objects"])

    summary = {
        "profile": profile.name,
        "objects": len(objects),
        "source_files": len({x.source_path for x in objects}),
        "parameters": len(param_rows),
        "reachable_inline_scripts": len(script_rows),
        "classes": {cls: sum(1 for obj in objects if object_class(obj) == cls) for cls in all_classes},
        "reports": {
            "objects": (out_dir / f"{profile.name}_objects.csv").as_posix(),
            "parameters": (out_dir / f"{profile.name}_parameters_after_expansion.csv").as_posix(),
            "inline_scripts": (out_dir / f"{profile.name}_reachable_inline_scripts.csv").as_posix(),
        },
    }
    write_text(out_dir / f"{profile.name}_analysis_summary.json", json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    parser.add_argument("--profile", required=True, choices=list_profiles(), help="Object profile to analyze")
    parser.add_argument("--out", default="/mnt/data/PIF_profiled_reports/analysis", help="Report output directory")
    args = parser.parse_args()
    print(json.dumps(analyze(args.profile, Path(args.out), args.planet, args.work_dir), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
