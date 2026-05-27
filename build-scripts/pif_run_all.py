#!/usr/bin/env python3
"""
Run the full profile-driven PIF pipeline.

Pipeline steps:
1. analyze vanilla objects;
2. analyze reachable inline scripts and split requirements;
3. generate the PIF object layer;
4. run static validation.

The same command works for districts, zones and future profiles.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from pif_analyze import analyze as analyze_objects
from pif_generate_layer import generate as generate_layer
from pif_profiles import get_profile, list_profiles
from pif_split_inline_scripts import analyze as analyze_inline_scripts
from pif_stellaris import add_common_args, write_text
from pif_validate_layer import validate as validate_layer


def run_all(profile_name: str, planet: str, out: Path, reports: Path, work_dir: str | None = None, clean: bool = False, sparse_empty: bool = False) -> dict:
    """Run all PIF pipeline steps for one profile."""
    profile = get_profile(profile_name)
    reports.mkdir(parents=True, exist_ok=True)

    analysis = analyze_objects(profile.name, reports / "analysis", planet, work_dir)
    inline = analyze_inline_scripts(profile.name, reports / "inline_scripts", planet, work_dir)
    generation = generate_layer(profile.name, planet, out, work_dir, clean=clean, sparse_empty=sparse_empty)
    validation = validate_layer(profile.name, planet, out, out / profile.validation_report_name, work_dir)

    summary = {
        "profile": profile.name,
        "analysis": analysis,
        "inline_scripts": inline,
        "generation": generation,
        "validation": validation,
    }
    write_text(reports / f"{profile.name}_run_all_summary.json", json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    parser.add_argument("--profile", required=True, choices=list_profiles(), help="Profile to run")
    parser.add_argument("--out", default=None, help="Generated PIF root")
    parser.add_argument("--reports", default="/mnt/data/PIF_profiled_reports", help="Report root")
    parser.add_argument("--clean", action="store_true", help="Delete generated output before generation")
    parser.add_argument("--sparse-empty", action="store_true", help="Skip empty category scripts for profiles that support it")
    args = parser.parse_args()
    profile = get_profile(args.profile)
    out = Path(args.out) if args.out else Path(profile.default_output)
    print(json.dumps(run_all(args.profile, args.planet, out, Path(args.reports) / profile.name, args.work_dir, args.clean, args.sparse_empty), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
