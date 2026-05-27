#!/usr/bin/env python3
"""
Profile-driven static validator for generated PIF object layers.

Validation compares the vanilla baseline with generated PIF output after the
normalizations accepted by the selected profile.  It is a static equivalence
check and does not replace an in-game smoke test.
"""
from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path

from pif_profiles import get_profile, list_profiles
from pif_stellaris import StellarisProject, add_common_args, load_project_from_args, write_text


def validate(profile_name: str, planet: str, generated: Path, out: Path, work_dir: str | None = None) -> dict:
    """Run the selected profile validator and normalize its summary shape."""
    profile = get_profile(profile_name)

    class Args:
        pass

    args = Args()
    args.planet = planet
    args.work_dir = work_dir
    vanilla_project = load_project_from_args(args)
    generated_project = StellarisProject(generated)
    backend = importlib.import_module(profile.validator_backend)

    if profile.name == "districts":
        report = backend.validate(vanilla_project, generated_project)
        write_text(out, json.dumps(report, indent=2, ensure_ascii=False) + "\n")
        summary = dict(report["summary"])
        summary["report"] = out.as_posix()
        return summary

    if profile.name in {"zones", "zone_slots", "buildings", "jobs"}:
        return backend.validate(vanilla_project, generated_project, out)

    raise NotImplementedError(profile.name)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    parser.add_argument("--profile", required=True, choices=list_profiles(), help="Profile to validate")
    parser.add_argument("--generated", required=True, help="Generated PIF root to validate")
    parser.add_argument("--out", default=None, help="Validation report JSON path")
    args = parser.parse_args()
    profile = get_profile(args.profile)
    out = Path(args.out) if args.out else Path(args.generated) / profile.validation_report_name
    print(json.dumps(validate(args.profile, args.planet, Path(args.generated), out, args.work_dir), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
