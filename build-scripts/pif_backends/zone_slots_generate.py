#!/usr/bin/env python3
"""
Generate the PIF stage-3 zone-slot layer from vanilla Stellaris zone_slots.

Generated structure:

* one ``common/zone_slots`` file per vanilla zone_slot object;
* ``start`` stays in the object root as METADATA;
* zone compatibility lists are moved to per-slot ``zs_config`` scripts;
* existence/unlock triggers are moved to per-slot ``availability`` scripts;
* no scripted variables are generated, because vanilla zone_slots contain no
  numeric tuning scalars or ``@variable`` references in the supported baseline;
* no vanilla inline scripts are copied, because vanilla zone_slots do not use
  inline scripts in the supported baseline.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

from pif_stellaris import (
    Atom,
    Block,
    Stmt,
    CANONICAL_ZONE_SLOT_CATEGORIES,
    add_common_args,
    clone_node,
    ensure_clean_dir,
    load_project_from_args,
    make_inline_script_stmt,
    render_file,
    top_level_stmts,
    write_text,
    zone_slot_category_for_param,
)


def render_script(items: List[Stmt]) -> str:
    """Render a category inline script file body."""
    if not items:
        return "# Empty PIF zone-slot category hook.\n"
    return "".join(render_file(Block([item])) for item in items)


def split_slot_body(body: Block) -> Tuple[List[Stmt], Dict[str, List[Stmt]]]:
    """Split an expanded zone_slot body into root metadata and categories."""
    root_items: List[Stmt] = []
    categories: Dict[str, List[Stmt]] = {cat: [] for cat in CANONICAL_ZONE_SLOT_CATEGORIES}

    for stmt in top_level_stmts(body):
        category = zone_slot_category_for_param(stmt.key)
        if category == "metadata":
            root_items.append(clone_node(stmt))
        elif category in categories:
            categories[category].append(clone_node(stmt))
        else:
            # Unknown top-level statements must stay in root so the generator is
            # conservative when future Stellaris versions add new slot keys.
            root_items.append(clone_node(stmt))
    return root_items, categories


def generate(project, output: Path, clean: bool = False) -> dict:
    """Generate the PIF zone_slots layer into ``output``."""
    if clean:
        ensure_clean_dir(output)
    else:
        output.mkdir(parents=True, exist_ok=True)

    slots = project.load_zone_slots()
    manifest_slots: List[dict] = []
    generated_category_scripts = 0

    for slot in slots:
        root_items, categories = split_slot_body(slot.expanded_body)
        object_file = output / "common" / "zone_slots" / f"pif_{slot.source_stem}_{slot.key}.txt"
        inline_base = output / "common" / "inline_scripts" / "pif" / "zone_slots" / slot.key

        object_items: List[Stmt] = list(root_items)
        category_files: Dict[str, str] = {}
        for category in CANONICAL_ZONE_SLOT_CATEGORIES:
            script_rel = f"pif/zone_slots/{slot.key}/{category}"
            object_items.append(make_inline_script_stmt(script_rel))
            script_path = inline_base / f"{category}.txt"
            write_text(script_path, render_script(categories[category]))
            category_files[category] = script_path.relative_to(output).as_posix()
            generated_category_scripts += 1

        write_text(
            object_file,
            f"# PIF normalized zone_slot object generated from {slot.source_path.relative_to(project.root).as_posix()}.\n"
            f"{render_file(Block([Stmt(slot.key, '=', Block(object_items))]))}",
        )
        manifest_slots.append(
            {
                "zone_slot": slot.key,
                "source_file": slot.source_path.relative_to(project.root).as_posix(),
                "generated_file": object_file.relative_to(output).as_posix(),
                "category_files": category_files,
                "category_statement_counts": {cat: len(categories[cat]) for cat in CANONICAL_ZONE_SLOT_CATEGORIES},
                "metadata_statement_count": len(root_items),
            }
        )

    manifest = {
        "profile": "zone_slots",
        "zone_slots": len(slots),
        "generated_object_files": len(slots),
        "generated_category_scripts": generated_category_scripts,
        "variable_files": 0,
        "variables": 0,
        "objects": manifest_slots,
    }
    write_text(output / "pif_zone_slot_generation_manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return {
        "profile": "zone_slots",
        "output": output.as_posix(),
        "zone_slots": len(slots),
        "generated_object_files": len(slots),
        "generated_category_scripts": generated_category_scripts,
        "variable_files": 0,
        "variables": 0,
        "manifest": (output / "pif_zone_slot_generation_manifest.json").as_posix(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    parser.add_argument("--out", default="/mnt/data/PIF_stage3_zone_slots", help="Generated PIF zone_slot output root")
    parser.add_argument("--clean", action="store_true", help="Delete output directory before generation")
    args = parser.parse_args()

    project = load_project_from_args(args)
    print(json.dumps(generate(project, Path(args.out), clean=args.clean), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
