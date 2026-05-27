#!/usr/bin/env python3
"""
Validate generated PIF districts against vanilla expanded districts.

The validator compares vanilla and PIF after accepted normalizations:
- vanilla planet_modifier is converted to triggered_planet_modifier with always=yes;
- numeric scalar literals and resolved @variables are compared as literal numbers;
- real district categories are compared within their semantic buckets, so the new PIF
  category layout does not fail validation just because cross-category order changed;
- district masks are compared as compact METADATA + MASK objects.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

from pif_stellaris import (
    Atom,
    Block,
    Stmt,
    add_common_args,
    category_for_param,
    clone_node,
    ensure_planet_root,
    is_numeric_literal,
    load_project_from_args,
    normalize_planet_modifier,
    render_node,
    top_level_stmts,
    StellarisProject,
)


def literalize_numeric_refs(node: Any, variables: Dict[str, str]) -> Any:
    if isinstance(node, Atom):
        if (not node.quoted) and node.value.startswith("@") and node.value in variables and is_numeric_literal(variables[node.value]):
            return Atom(variables[node.value], quoted=False)
        return clone_node(node)
    if isinstance(node, Stmt):
        return Stmt(node.key, node.op, literalize_numeric_refs(node.value, variables))
    if isinstance(node, Block):
        return Block([literalize_numeric_refs(x, variables) for x in node.items])
    return clone_node(node)


def normalized_real_buckets(block: Block, variables: Dict[str, str], district_class: str = "real") -> Dict[str, List[str]]:
    buckets: Dict[str, List[str]] = defaultdict(list)
    for stmt in top_level_stmts(block):
        for out_stmt in normalize_planet_modifier(stmt):
            lit = literalize_numeric_refs(out_stmt, variables)
            cat = category_for_param(out_stmt.key, district_class=district_class)
            if cat == "unknown":
                cat = "metadata"
            buckets[cat].append(render_node(lit, 0))
    return dict(buckets)


def normalized_mask_sequence(block: Block, variables: Dict[str, str]) -> List[str]:
    out: List[str] = []
    for stmt in top_level_stmts(block):
        cat = category_for_param(stmt.key, district_class="active_mask")
        if cat == "unknown":
            continue
        out.append(render_node(literalize_numeric_refs(stmt, variables), 0))
    return out


def load_generated_districts(pif_project: StellarisProject) -> Dict[str, Tuple[Path, Block]]:
    result: Dict[str, Tuple[Path, Block]] = {}
    for key, path, body in pif_project.load_top_level_objects("districts", prefix="district_"):
        result[key] = (path, body)
    return result


def compare_lists(expected: List[str], actual: List[str]) -> Dict[str, Any]:
    if expected == actual:
        return {"ok": True}
    return {
        "ok": False,
        "expected_count": len(expected),
        "actual_count": len(actual),
        "first_expected_only": [x for x in expected if x not in actual][:10],
        "first_actual_only": [x for x in actual if x not in expected][:10],
    }


def validate(vanilla_project: StellarisProject, pif_project: StellarisProject) -> Dict[str, Any]:
    generated = load_generated_districts(pif_project)
    results = []

    for d in vanilla_project.load_districts():
        local_vars = vanilla_project.collect_local_variables(d.source_path)
        vanilla_vars = {**vanilla_project.global_variables, **local_vars}
        row: Dict[str, Any] = {
            "district": d.key,
            "class": d.class_name,
            "vanilla_source": d.source_path.relative_to(vanilla_project.root).as_posix(),
        }
        if d.key not in generated:
            row["ok"] = False
            row["error"] = "missing generated district"
            results.append(row)
            continue

        generated_path, generated_body = generated[d.key]
        generated_expanded = pif_project.expand_block(generated_body)
        row["generated_source"] = generated_path.relative_to(pif_project.root).as_posix()

        if d.class_name == "real":
            expected = normalized_real_buckets(d.expanded_body, vanilla_vars, "real")
            actual = normalized_real_buckets(generated_expanded, pif_project.global_variables, "real")
            cats = sorted(set(expected) | set(actual))
            cat_results = {cat: compare_lists(expected.get(cat, []), actual.get(cat, [])) for cat in cats}
            row["category_results"] = cat_results
            row["ok"] = all(x["ok"] for x in cat_results.values())
        else:
            expected_seq = normalized_mask_sequence(d.expanded_body, vanilla_vars)
            actual_seq = normalized_mask_sequence(generated_expanded, pif_project.global_variables)
            seq_result = compare_lists(expected_seq, actual_seq)
            row["sequence_result"] = seq_result
            row["ok"] = seq_result["ok"]
        results.append(row)

    return {
        "summary": {
            "checked": len(results),
            "ok": sum(1 for x in results if x.get("ok")),
            "failed": sum(1 for x in results if not x.get("ok")),
        },
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    parser.add_argument("--pif-root", default="/mnt/data/PIF_stage1", help="Generated PIF root to validate")
    parser.add_argument("--out", default="/mnt/data/PIF_stage1_validation.json", help="Validation JSON report")
    args = parser.parse_args()

    vanilla_project = load_project_from_args(args)
    
    pif_root = Path(args.pif_root)
    if (pif_root / "common" / "districts").exists():
        pif_root = pif_root / "common"
    pif_project = StellarisProject(pif_root)
    report = validate(vanilla_project, pif_project)
    Path(args.out).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
