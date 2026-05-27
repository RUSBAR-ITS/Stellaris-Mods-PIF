#!/usr/bin/env python3
"""
Profile-driven inline script split analysis for PIF.

This command does not copy vanilla inline scripts into the mod.  It classifies
reachable vanilla inline scripts as either category-compatible (WHOLE) or mixed
(SPLIT) for the selected profile.  The generated PIF layer expands and rewrites
script content into PIF category files; vanilla helper scripts are not emitted as
runtime files by default.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Set

from pif_profiles import get_profile, list_profiles
from pif_stellaris import Block, Stmt, add_common_args, load_project_from_args, top_level_stmts, write_text


def load_objects(project, profile):
    """Load profile objects from the vanilla baseline."""
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


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    """Write a CSV file with stable column order."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def classify_inline_script(project, profile, script_key: str) -> Dict[str, Any]:
    """Classify one inline script by categories present after expansion."""
    raw = project.parse_inline_script(script_key)
    expanded = project.expand_block(raw)
    category_counts: Counter[str] = Counter()
    parameters: Counter[str] = Counter()
    for stmt in top_level_stmts(expanded):
        parameters[stmt.key] += 1
        if profile.name == "buildings":
            from pif_backends.buildings_common import split_building_statement

            categorized = split_building_statement(stmt)
            if not categorized:
                category_counts["metadata"] += 1
            for category, _out_stmt in categorized:
                if category == "unknown":
                    category = "metadata"
                category_counts[category] += 1
        elif profile.name == "jobs":
            from pif_backends.jobs_common import split_job_statement

            categorized = split_job_statement(stmt)
            if not categorized:
                category_counts["metadata"] += 1
            for category, _out_stmt in categorized:
                if category == "unknown":
                    category = "metadata"
                category_counts[category] += 1
        else:
            category = profile.category_for_param(stmt.key, object_class="real" if profile.name == "districts" else "zone")
            if category == "unknown":
                category = "metadata"
            category_counts[category] += 1
    categories = sorted(category_counts)
    decision = "WHOLE" if len(set(categories) - {"metadata"}) <= 1 and len(categories) <= 2 else "SPLIT"
    # If a script contains only metadata, it can still be used whole as a single
    # category fragment.  If metadata is mixed with a behavior category, it must
    # be split because root metadata and category scripts have different owners.
    if "metadata" in categories and len(categories) > 1:
        decision = "SPLIT"
    return {
        "inline_script": script_key,
        "decision": decision,
        "categories": " ".join(categories),
        "category_counts": dict(category_counts),
        "parameters": " ".join(sorted(parameters)),
        "parameter_counts": dict(parameters),
    }


def analyze(profile_name: str, out_dir: Path, planet: str, work_dir: str | None = None) -> Dict[str, Any]:
    """Analyze reachable inline scripts for the selected profile."""
    profile = get_profile(profile_name)

    class Args:
        pass

    args = Args()
    args.planet = planet
    args.work_dir = work_dir
    project = load_project_from_args(args)
    objects = load_objects(project, profile)
    out_dir.mkdir(parents=True, exist_ok=True)

    reachable: Set[str] = set()
    direct_rows: List[Dict[str, Any]] = []
    nested_edges: Set[tuple[str, str]] = set()

    for obj in objects:
        for script in project.reachable_inline_scripts_from_block(obj.body):
            reachable.add(script)
        for stmt in top_level_stmts(obj.body):
            if isinstance(stmt, Stmt) and stmt.key == "inline_script":
                # Direct-call reporting is best-effort: nested calls are fully
                # represented in the reachable set and edge report below.
                direct_rows.append({"object": obj.key, "inline_script_value": str(stmt.value)})

    for script in sorted(reachable):
        try:
            block = project.parse_inline_script(script)
        except Exception:
            continue
        for nested in project.reachable_inline_scripts_from_block(block):
            nested_edges.add((script, nested))

    summary_rows = [classify_inline_script(project, profile, script) for script in sorted(reachable)]
    write_csv(out_dir / f"{profile.name}_inline_scripts_summary.csv", summary_rows, ["inline_script", "decision", "categories", "parameters", "category_counts", "parameter_counts"])
    write_csv(out_dir / f"{profile.name}_inline_direct_calls.csv", direct_rows, ["object", "inline_script_value"])
    write_csv(out_dir / f"{profile.name}_inline_nested_edges.csv", [{"from": a, "to": b} for a, b in sorted(nested_edges)], ["from", "to"])

    summary = {
        "profile": profile.name,
        "reachable_inline_scripts": len(summary_rows),
        "whole": sum(1 for r in summary_rows if r["decision"] == "WHOLE"),
        "split": sum(1 for r in summary_rows if r["decision"] == "SPLIT"),
        "reports": {
            "summary_csv": (out_dir / f"{profile.name}_inline_scripts_summary.csv").as_posix(),
            "direct_calls_csv": (out_dir / f"{profile.name}_inline_direct_calls.csv").as_posix(),
            "nested_edges_csv": (out_dir / f"{profile.name}_inline_nested_edges.csv").as_posix(),
        },
    }
    write_text(out_dir / f"{profile.name}_inline_script_split_summary.json", json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    parser.add_argument("--profile", required=True, choices=list_profiles(), help="Profile to analyze")
    parser.add_argument("--out", default="/mnt/data/PIF_profiled_reports/inline_scripts", help="Report output directory")
    args = parser.parse_args()
    print(json.dumps(analyze(args.profile, Path(args.out), args.planet, args.work_dir), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
