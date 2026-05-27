#!/usr/bin/env python3
"""
Profile-driven generation command for PIF object layers.

The command delegates profile-specific transformation details to backend modules
while keeping a single CLI for all supported object families.  The profile tells
this script which backend to load and what default output path to use.
"""
from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path

from pif_profiles import get_profile, list_profiles
from pif_stellaris import add_common_args, load_project_from_args


def generate(profile_name: str, planet: str, out: Path | None, work_dir: str | None = None, clean: bool = False, sparse_empty: bool = False) -> dict:
    """Generate one PIF layer using the selected profile backend."""
    profile = get_profile(profile_name)

    class Args:
        pass

    args = Args()
    args.planet = planet
    args.work_dir = work_dir
    project = load_project_from_args(args)
    backend = importlib.import_module(profile.generator_backend)
    output = out or Path(profile.default_output)

    # Zone generation supports sparse empty category files.  District generation
    # intentionally does not use that option because lifecycle/extension hooks
    # for real districts are part of the current district specification.
    if profile.name in {"zones", "buildings", "jobs"}:
        return backend.generate(project, output, clean=clean, sparse_empty=sparse_empty)
    return backend.generate(project, output, clean=clean)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    parser.add_argument("--profile", required=True, choices=list_profiles(), help="Profile to generate")
    parser.add_argument("--out", default=None, help="Generated PIF root. Defaults to the profile output path")
    parser.add_argument("--clean", action="store_true", help="Delete output directory before generation")
    parser.add_argument("--sparse-empty", action="store_true", help="For profiles that support it, skip empty category scripts")
    args = parser.parse_args()
    print(json.dumps(generate(args.profile, args.planet, Path(args.out) if args.out else None, args.work_dir, args.clean, args.sparse_empty), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
