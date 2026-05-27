#!/usr/bin/env python3
"""
Validate a generated PIF zone layer against the vanilla Stellaris baseline.

Validation is static.  It does not replace an in-game smoke test, but it checks
that the generated PIF zones expand to the same canonical category content as the
vanilla zones after accepted PIF normalizations:

* static zone modifiers are normalized to triggered modifier blocks;
* numeric PIF variables are resolved back to literal values;
* vanilla numeric ``@variables`` are resolved where possible;
* visual-swap weights remain literal and are compared as-is.

The validator compares canonical category buckets instead of raw file order,
because PIF intentionally moves behavior into category inline scripts.  Order is
still preserved inside each category bucket and repeated block sequence.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from pif_stellaris import (
    Block,
    Stmt,
    add_common_args,
    load_project_from_args,
    render_file,
    replace_variables_for_compare,
    write_text,
)
from pif_backends.zones_generate import bucket_zone


def canonical_zone_buckets(project, zone_body: Block, source_vars: Dict[str, str]) -> Dict[str, str]:
    """Return rendered canonical buckets for an expanded zone body."""
    body = replace_variables_for_compare(zone_body, source_vars)
    buckets, unknown = bucket_zone(body)
    return {category: render_file(Block(items)).strip() for category, items in sorted(buckets.items())}


def validate(vanilla_project, generated_project, out_path: Path) -> Dict[str, object]:
    """Validate generated zones and write a JSON report."""
    vanilla_zones = {zone.key: zone for zone in vanilla_project.load_zones()}
    generated_zones = {zone.key: zone for zone in generated_project.load_zones()}

    rows: List[Dict[str, object]] = []
    ok = 0
    failed = 0

    for key in sorted(vanilla_zones):
        vanilla = vanilla_zones[key]
        generated = generated_zones.get(key)
        if generated is None:
            failed += 1
            rows.append({"zone": key, "status": "FAIL", "reason": "missing generated zone"})
            continue

        vanilla_vars = {**vanilla_project.global_variables, **vanilla_project.collect_local_variables(vanilla.source_path)}
        generated_vars = generated_project.global_variables
        vanilla_canonical = canonical_zone_buckets(vanilla_project, vanilla.expanded_body, vanilla_vars)
        generated_canonical = canonical_zone_buckets(generated_project, generated.expanded_body, generated_vars)

        if vanilla_canonical == generated_canonical:
            ok += 1
            rows.append({"zone": key, "status": "OK"})
            continue

        failed += 1
        differing = sorted(set(vanilla_canonical) | set(generated_canonical))
        differing = [c for c in differing if vanilla_canonical.get(c) != generated_canonical.get(c)]
        rows.append(
            {
                "zone": key,
                "status": "FAIL",
                "reason": "canonical category mismatch",
                "differing_categories": differing,
                "vanilla": {c: vanilla_canonical.get(c, "") for c in differing},
                "generated": {c: generated_canonical.get(c, "") for c in differing},
            }
        )

    extra = sorted(set(generated_zones) - set(vanilla_zones))
    for key in extra:
        failed += 1
        rows.append({"zone": key, "status": "FAIL", "reason": "extra generated zone"})

    report = {"checked": len(vanilla_zones), "ok": ok, "failed": failed, "rows": rows}
    write_text(out_path, json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    return {"checked": len(vanilla_zones), "ok": ok, "failed": failed, "report": out_path.as_posix()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    parser.add_argument("--generated", default="/mnt/data/PIF_stage2_zones", help="Generated PIF zone output root")
    parser.add_argument("--out", default="/mnt/data/PIF_stage2_zones/pif_zone_validation_report.json", help="Validation report JSON path")
    args = parser.parse_args()

    vanilla_project = load_project_from_args(args)
    generated_project = __import__("pif_stellaris").StellarisProject(Path(args.generated))
    print(json.dumps(validate(vanilla_project, generated_project, Path(args.out)), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
