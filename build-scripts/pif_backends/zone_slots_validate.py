#!/usr/bin/env python3
"""
Validate generated PIF zone_slots against the vanilla Stellaris baseline.

Validation expands PIF category inline scripts in-place and compares the result
with expanded vanilla zone_slot objects.  There are currently no zone-slot
statement normalizations and no variable substitutions required by the accepted
PIF stage-3 rules.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

from pif_stellaris import (
    Block,
    Stmt,
    add_common_args,
    load_project_from_args,
    render_file,
    write_text,
)


def canonical_slot_text(body: Block) -> str:
    """Render a zone_slot body to deterministic text for comparison."""
    return render_file(Block([Stmt("_", "=", body)]))


def validate(vanilla_project, generated_project, out_path: Path) -> dict:
    """Validate generated zone_slot objects and write a JSON report."""
    vanilla_slots = {slot.key: slot for slot in vanilla_project.load_zone_slots()}
    generated_slots = {slot.key: slot for slot in generated_project.load_zone_slots()}

    rows: List[dict] = []
    ok = 0
    failed = 0

    for key in sorted(vanilla_slots):
        vanilla = vanilla_slots[key]
        generated = generated_slots.get(key)
        if generated is None:
            failed += 1
            rows.append({"zone_slot": key, "status": "FAIL", "reason": "missing generated zone_slot"})
            continue

        vanilla_text = canonical_slot_text(vanilla.expanded_body)
        generated_text = canonical_slot_text(generated.expanded_body)
        if vanilla_text == generated_text:
            ok += 1
            rows.append({"zone_slot": key, "status": "OK"})
        else:
            failed += 1
            rows.append(
                {
                    "zone_slot": key,
                    "status": "FAIL",
                    "reason": "expanded body differs",
                    "vanilla": vanilla_text,
                    "generated": generated_text,
                }
            )

    for key in sorted(set(generated_slots) - set(vanilla_slots)):
        failed += 1
        rows.append({"zone_slot": key, "status": "FAIL", "reason": "extra generated zone_slot"})

    report = {"checked": len(vanilla_slots), "ok": ok, "failed": failed, "rows": rows}
    write_text(out_path, json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    return {"checked": len(vanilla_slots), "ok": ok, "failed": failed, "report": out_path.as_posix()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    parser.add_argument("--generated", default="/mnt/data/PIF_stage3_zone_slots", help="Generated PIF zone_slot output root")
    parser.add_argument("--out", default="/mnt/data/PIF_stage3_zone_slots/pif_zone_slot_validation_report.json", help="Validation report JSON path")
    args = parser.parse_args()

    vanilla_project = load_project_from_args(args)
    generated_project = __import__("pif_stellaris").StellarisProject(Path(args.generated))
    print(json.dumps(validate(vanilla_project, generated_project, Path(args.out)), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
