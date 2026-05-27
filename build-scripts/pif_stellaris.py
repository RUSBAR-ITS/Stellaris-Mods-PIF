#!/usr/bin/env python3
"""
Shared Stellaris/PIF utilities for Planetary Infrastructure Framework scripts.

The module intentionally implements a small, deterministic subset of the Stellaris
script language that is sufficient for static transformation of planet
infrastructure objects.  It is not intended to be a full game parser.  The most
important design goals are:

* preserve statement order inside parsed blocks;
* expand inline_script calls recursively in-place;
* keep comments out of the AST, because comments are not gameplay data;
* provide object loaders for vanilla districts, zones, zone_slots and buildings;
* provide normalization helpers used by PIF generators and validators.

All comments and docstrings in scripts are written in English by project rule.
User-facing documentation is provided separately in Russian.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import zipfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple


# -----------------------------------------------------------------------------
# AST model
# -----------------------------------------------------------------------------


@dataclass
class Atom:
    """A scalar script token.

    The parser keeps the quotation flag so that rendering can preserve strings
    such as localization keys and script paths when they were originally quoted.
    """

    value: str
    quoted: bool = False


@dataclass
class Stmt:
    """A key/operator/value statement, for example ``resources = { ... }``."""

    key: str
    op: str
    value: Any


@dataclass
class Block:
    """A Stellaris script block or a list of top-level statements."""

    items: List[Any] = field(default_factory=list)


class ParseError(Exception):
    """Raised when the lightweight parser cannot parse a script file."""


# -----------------------------------------------------------------------------
# Parser / renderer
# -----------------------------------------------------------------------------


def strip_comments(text: str) -> str:
    """Remove ``#`` comments while preserving quoted strings."""
    out: List[str] = []
    i = 0
    in_quote = False
    escaped = False
    while i < len(text):
        ch = text[i]
        if in_quote:
            out.append(ch)
            if ch == "\\" and not escaped:
                escaped = True
            elif ch == '"' and not escaped:
                in_quote = False
                escaped = False
            else:
                escaped = False
            i += 1
            continue
        if ch == '"':
            in_quote = True
            out.append(ch)
            i += 1
            continue
        if ch == "#":
            while i < len(text) and text[i] not in "\r\n":
                i += 1
            if i < len(text):
                out.append(text[i])
                i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def tokenize(text: str) -> List[Tuple[str, str]]:
    """Tokenize a small subset of the Stellaris script language."""
    text = strip_comments(text)
    tokens: List[Tuple[str, str]] = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch.isspace():
            i += 1
            continue
        if ch in "{}":
            tokens.append((ch, ch))
            i += 1
            continue
        if i + 1 < len(text) and text[i : i + 2] in (">=", "<=", "!=", "?=", "=="):
            tokens.append(("OP", text[i : i + 2]))
            i += 2
            continue
        if ch in "=<>":
            tokens.append(("OP", ch))
            i += 1
            continue
        if ch == '"':
            j = i + 1
            value: List[str] = []
            escaped = False
            while j < len(text):
                cur = text[j]
                if cur == "\\" and not escaped:
                    escaped = True
                    value.append(cur)
                    j += 1
                    continue
                if cur == '"' and not escaped:
                    break
                value.append(cur)
                escaped = False
                j += 1
            if j >= len(text):
                raise ParseError("unterminated quoted string")
            tokens.append(("STRING", "".join(value)))
            i = j + 1
            continue
        j = i
        while j < len(text) and (not text[j].isspace()) and text[j] not in "{}=<>":
            j += 1
        if j == i:
            raise ParseError(f"unexpected character {text[i]!r} at offset {i}")
        tokens.append(("ATOM", text[i:j]))
        i = j
    return tokens


class Parser:
    """Recursive-descent parser for the token stream."""

    def __init__(self, tokens: Sequence[Tuple[str, str]]):
        self.tokens = list(tokens)
        self.i = 0

    def peek(self, offset: int = 0) -> Optional[Tuple[str, str]]:
        pos = self.i + offset
        return self.tokens[pos] if pos < len(self.tokens) else None

    def pop(self) -> Tuple[str, str]:
        tok = self.peek()
        if tok is None:
            raise ParseError("unexpected EOF")
        self.i += 1
        return tok

    def parse(self) -> Block:
        return self.parse_block(until=None)

    def parse_block(self, until: Optional[str] = "}") -> Block:
        items: List[Any] = []
        while self.i < len(self.tokens):
            cur = self.peek()
            if until and cur and cur[0] == until:
                self.pop()
                break
            nxt = self.peek(1)
            if cur and cur[0] in ("ATOM", "STRING") and nxt and nxt[0] == "OP":
                key = self.pop()[1]
                op = self.pop()[1]
                items.append(Stmt(key, op, self.parse_value()))
                continue
            tok = self.pop()
            if tok[0] == "{":
                items.append(self.parse_block("}"))
            elif tok[0] in ("ATOM", "STRING"):
                items.append(Atom(tok[1], quoted=(tok[0] == "STRING")))
            elif tok[0] == "OP":
                items.append(Atom(tok[1], quoted=False))
            elif tok[0] == "}":
                if until:
                    break
                raise ParseError("unexpected }")
        return Block(items)

    def parse_value(self) -> Any:
        tok = self.pop()
        if tok[0] == "{":
            return self.parse_block("}")
        if tok[0] in ("ATOM", "STRING"):
            return Atom(tok[1], quoted=(tok[0] == "STRING"))
        if tok[0] == "OP":
            return Atom(tok[1], quoted=False)
        raise ParseError(f"bad value token {tok!r}")


def parse_text(text: str) -> Block:
    """Parse raw script text into a top-level block."""
    return Parser(tokenize(text)).parse()


def quote_atom(value: str) -> str:
    return '"' + value.replace('"', '\\"') + '"'


def render_node(node: Any, indent: int = 0) -> str:
    """Render an AST node back to script text using tab indentation."""
    tab = "\t"
    prefix = tab * indent
    if isinstance(node, Atom):
        return quote_atom(node.value) if node.quoted else node.value
    if isinstance(node, Stmt):
        return f"{node.key} {node.op} {render_node(node.value, indent)}"
    if isinstance(node, Block):
        if not node.items:
            return "{}"
        lines = ["{"]
        for item in node.items:
            lines.append(f"{tab * (indent + 1)}{render_node(item, indent + 1)}")
        lines.append(prefix + "}")
        return "\n".join(lines)
    return str(node)


def render_file(block: Block) -> str:
    """Render a top-level block as a full script file body."""
    return "\n\n".join(render_node(item, 0) for item in block.items).rstrip() + "\n"


def clone_node(node: Any) -> Any:
    """Deep-copy an AST node while keeping dataclass types."""
    if isinstance(node, Atom):
        return Atom(node.value, node.quoted)
    if isinstance(node, Stmt):
        return Stmt(node.key, node.op, clone_node(node.value))
    if isinstance(node, Block):
        return Block([clone_node(item) for item in node.items])
    return node


# -----------------------------------------------------------------------------
# File/project loading
# -----------------------------------------------------------------------------


def ensure_planet_root(path_or_zip: Path, work_dir: Optional[Path] = None) -> Path:
    """Return a directory containing extracted Planet archive contents."""
    path_or_zip = Path(path_or_zip)
    if path_or_zip.is_dir():
        return path_or_zip
    if not path_or_zip.exists():
        raise FileNotFoundError(path_or_zip)
    if path_or_zip.suffix.lower() != ".zip":
        raise ValueError(f"expected Planet directory or .zip, got {path_or_zip}")
    work_dir = Path(work_dir or path_or_zip.with_suffix(""))
    if work_dir.exists() and any(work_dir.iterdir()):
        maybe_planet = work_dir / "Planet"
        return maybe_planet if maybe_planet.is_dir() else work_dir
    work_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path_or_zip, "r") as zf:
        zf.extractall(work_dir)
    maybe_planet = work_dir / "Planet"
    return maybe_planet if maybe_planet.is_dir() else work_dir


@dataclass
class DistrictObject:
    """Loaded vanilla or generated district object."""

    key: str
    source_path: Path
    source_stem: str
    body: Block
    expanded_body: Block
    class_name: str


@dataclass
class ZoneObject:
    """Loaded vanilla or generated zone object."""

    key: str
    source_path: Path
    source_stem: str
    body: Block
    expanded_body: Block


@dataclass
class ZoneSlotObject:
    """Loaded vanilla or generated zone slot object."""

    key: str
    source_path: Path
    source_stem: str
    body: Block
    expanded_body: Block


@dataclass
class BuildingObject:
    """Loaded vanilla or generated building object."""

    key: str
    source_path: Path
    source_stem: str
    body: Block
    expanded_body: Block
    class_name: str


@dataclass
class JobObject:
    """Loaded vanilla or generated pop job object."""

    key: str
    source_path: Path
    source_stem: str
    body: Block
    expanded_body: Block
    class_name: str


class StellarisProject:
    """Project view over a Planet archive or a generated PIF output tree."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.inline_scripts = self._collect_inline_scripts()
        self.global_variables = self._collect_scripted_variables()

    def _collect_inline_scripts(self) -> Dict[str, Path]:
        result: Dict[str, Path] = {}
        base = self.root / "inline_scripts"
        if not base.exists():
            base = self.root / "common" / "inline_scripts"
        if not base.exists():
            return result
        for path in sorted(base.rglob("*.txt")):
            if path.name.upper().startswith("00_README"):
                continue
            result[path.relative_to(base).with_suffix("").as_posix()] = path
        return result

    def _collect_scripted_variables(self) -> Dict[str, str]:
        result: Dict[str, str] = {}
        bases = [self.root / "scripted_variables", self.root / "common" / "scripted_variables"]
        for base in bases:
            if not base.exists():
                continue
            for path in sorted(base.rglob("*.txt")):
                try:
                    ast = parse_text(path.read_text(encoding="utf-8-sig"))
                except ParseError:
                    continue
                for item in ast.items:
                    if isinstance(item, Stmt) and item.key.startswith("@") and isinstance(item.value, Atom):
                        result[item.key] = item.value.value
        return result

    def collect_local_variables(self, path: Path) -> Dict[str, str]:
        """Collect ``@`` variables declared at the top level of a source file."""
        result: Dict[str, str] = {}
        ast = parse_text(path.read_text(encoding="utf-8-sig"))
        for item in ast.items:
            if isinstance(item, Stmt) and item.key.startswith("@") and isinstance(item.value, Atom):
                result[item.key] = item.value.value
        return result

    def inline_script_path(self, script: str) -> Path:
        key = normalize_script_key(script)
        if key not in self.inline_scripts:
            raise FileNotFoundError(f"inline_script not found: {script}")
        return self.inline_scripts[key]

    def read_script(self, script: str) -> str:
        return self.inline_script_path(script).read_text(encoding="utf-8-sig")

    def parse_inline_script(self, script: str, params: Optional[Dict[str, str]] = None) -> Block:
        """Parse an inline script after simple ``$PARAM$`` substitution."""
        return parse_text(substitute_params(self.read_script(script), params or {}))

    def expand_block(self, block: Block, stack: Tuple[str, ...] = ()) -> Block:
        """Recursively expand inline_script calls in-place."""
        out: List[Any] = []
        for item in block.items:
            if isinstance(item, Stmt) and item.key == "inline_script" and item.op == "=":
                script, params = parse_inline_script_call(item.value)
                script_key = normalize_script_key(script)
                if script_key in stack:
                    raise RecursionError("inline_script recursion: " + " -> ".join(stack + (script_key,)))
                expanded = self.expand_block(self.parse_inline_script(script_key, params), stack + (script_key,))
                out.extend(expanded.items)
            elif isinstance(item, Stmt):
                value = self.expand_block(item.value, stack) if isinstance(item.value, Block) else clone_node(item.value)
                out.append(Stmt(item.key, item.op, value))
            elif isinstance(item, Block):
                out.append(self.expand_block(item, stack))
            else:
                out.append(clone_node(item))
        return Block(out)

    def reachable_inline_scripts_from_block(self, block: Block, stack: Tuple[str, ...] = ()) -> Iterator[str]:
        """Yield direct and nested inline script keys referenced by a block."""
        for item in block.items:
            if isinstance(item, Stmt):
                if item.key == "inline_script" and item.op == "=":
                    script, params = parse_inline_script_call(item.value)
                    script_key = normalize_script_key(script)
                    yield script_key
                    if script_key not in stack:
                        ast = self.parse_inline_script(script_key, params)
                        yield from self.reachable_inline_scripts_from_block(ast, stack + (script_key,))
                if isinstance(item.value, Block):
                    yield from self.reachable_inline_scripts_from_block(item.value, stack)
            elif isinstance(item, Block):
                yield from self.reachable_inline_scripts_from_block(item, stack)

    def load_top_level_objects(self, folder: str, prefix: Optional[str] = None) -> List[Tuple[str, Path, Block]]:
        """Load top-level keyed objects from a folder.

        Vanilla archives use folders at the root (``zones``), while generated PIF
        outputs use ``common/<folder>``.  Both locations are supported.
        """
        result: List[Tuple[str, Path, Block]] = []
        bases = [self.root / folder, self.root / "common" / folder]
        for base in bases:
            if not base.exists():
                continue
            for path in sorted(base.glob("*.txt")):
                if "DOCUMENTATION" in path.name or path.name.startswith("99_HOW"):
                    continue
                ast = parse_text(path.read_text(encoding="utf-8-sig"))
                for item in ast.items:
                    if isinstance(item, Stmt) and isinstance(item.value, Block):
                        if prefix is None or item.key.startswith(prefix):
                            result.append((item.key, path, item.value))
        return result

    def load_zones(self) -> List[ZoneObject]:
        """Load and expand all zone objects."""
        result: List[ZoneObject] = []
        for key, path, body in self.load_top_level_objects("zones"):
            expanded = self.expand_block(body)
            result.append(ZoneObject(key, path, path.stem, body, expanded))
        return result

    def load_zone_slots(self) -> List[ZoneSlotObject]:
        """Load and expand all zone slot objects."""
        result: List[ZoneSlotObject] = []
        for key, path, body in self.load_top_level_objects("zone_slots", prefix="slot_"):
            expanded = self.expand_block(body)
            result.append(ZoneSlotObject(key, path, path.stem, body, expanded))
        return result

    def load_buildings(self) -> List[BuildingObject]:
        """Load, expand and classify all building-like objects.

        Stage 4 must load every top-level object from common/buildings, not only
        keys with the building_ prefix.  Holdings and special non-building keys
        are valid vanilla building objects.
        """
        result: List[BuildingObject] = []
        for key, path, body in self.load_top_level_objects("buildings"):
            expanded = self.expand_block(body)
            class_name = classify_building_object(key, expanded)
            result.append(BuildingObject(key, path, path.stem, body, expanded, class_name))
        return result

    def load_jobs(self) -> List[JobObject]:
        """Load, expand and classify all pop job objects.

        Stage 5 loads every top-level block from common/pop_jobs.  Some valid
        vanilla jobs have no category field, so classification is report-only
        and must never be used as a load filter.
        """
        result: List[JobObject] = []
        for key, path, body in self.load_top_level_objects("pop_jobs"):
            expanded = self.expand_block(body)
            class_name = classify_job_object(key, expanded)
            result.append(JobObject(key, path, path.stem, body, expanded, class_name))
        return result

    def active_district_masks(self) -> set[str]:
        """Return district mask keys referenced by zone ``swap_type`` fields."""
        active: set[str] = set()
        for zone in self.load_zones():
            for stmt in iter_stmts(zone.expanded_body):
                if stmt.key == "swap_type" and isinstance(stmt.value, Atom):
                    active.add(stmt.value.value)
        return active

    def load_districts(self) -> List[DistrictObject]:
        """Load and classify all district objects.

        This is retained so that stage-2 scripts can reuse the same common module
        without breaking stage-1 district workflows.
        """
        active_masks = self.active_district_masks()
        result: List[DistrictObject] = []
        for key, path, body in self.load_top_level_objects("districts", prefix="district_"):
            expanded = self.expand_block(body)
            is_mask = is_district_mask(expanded)
            if is_mask and key in active_masks:
                class_name = "active_mask"
            elif is_mask:
                class_name = "sleeping_mask"
            else:
                class_name = "real"
            result.append(DistrictObject(key, path, path.stem, body, expanded, class_name))
        return result


# -----------------------------------------------------------------------------
# Inline script calls / parameters
# -----------------------------------------------------------------------------


def normalize_script_key(script: str) -> str:
    """Normalize an inline script reference to a key without ``.txt``."""
    key = script.strip().strip('"')
    return key[:-4] if key.endswith(".txt") else key


def substitute_params(text: str, params: Dict[str, str]) -> str:
    """Apply simple ``$NAME$`` inline-script parameter substitution."""

    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        return params.get(key, match.group(0))

    return re.sub(r"\$([A-Za-z0-9_]+)\$", repl, text)


def value_to_param_text(value: Any) -> str:
    if isinstance(value, Atom):
        return quote_atom(value.value) if value.quoted else value.value
    return render_node(value, 0)


def parse_inline_script_call(value: Any) -> Tuple[str, Dict[str, str]]:
    """Parse ``inline_script = ...`` value into script key and parameters."""
    if isinstance(value, Atom):
        return value.value, {}
    if isinstance(value, Block):
        script: Optional[str] = None
        params: Dict[str, str] = {}
        for item in value.items:
            if not isinstance(item, Stmt):
                continue
            if item.key == "script":
                script = item.value.value if isinstance(item.value, Atom) else render_node(item.value, 0)
            else:
                params[item.key] = value_to_param_text(item.value)
        if not script:
            raise ValueError(f"inline_script block has no script field: {render_node(value)}")
        return script, params
    raise ValueError(f"unsupported inline_script value: {value!r}")


# -----------------------------------------------------------------------------
# Traversal helpers
# -----------------------------------------------------------------------------


def iter_stmts(block: Block) -> Iterator[Stmt]:
    """Yield every statement recursively."""
    for item in block.items:
        if isinstance(item, Stmt):
            yield item
            if isinstance(item.value, Block):
                yield from iter_stmts(item.value)
        elif isinstance(item, Block):
            yield from iter_stmts(item)


def top_level_stmts(block: Block) -> Iterator[Stmt]:
    """Yield only top-level statements from a block."""
    for item in block.items:
        if isinstance(item, Stmt):
            yield item


def block_get_all(block: Block, key: str) -> List[Any]:
    return [stmt.value for stmt in top_level_stmts(block) if stmt.key == key]


# -----------------------------------------------------------------------------
# District classification retained for stage-1 compatibility
# -----------------------------------------------------------------------------


def is_always_no(value: Any) -> bool:
    return (
        isinstance(value, Block)
        and len(value.items) == 1
        and isinstance(value.items[0], Stmt)
        and value.items[0].key == "always"
        and isinstance(value.items[0].value, Atom)
        and value.items[0].value.value == "no"
    )


def is_slot_empty(value: Any) -> bool:
    return (
        isinstance(value, Block)
        and len(value.items) == 1
        and isinstance(value.items[0], Atom)
        and value.items[0].value == "slot_empty"
    )


def is_district_mask(expanded_body: Block) -> bool:
    zone_slots = block_get_all(expanded_body, "zone_slots")
    potentials = block_get_all(expanded_body, "potential")
    shows = block_get_all(expanded_body, "show_on_uncolonized")
    return bool(zone_slots and potentials and shows) and is_slot_empty(zone_slots[0]) and is_always_no(potentials[0]) and is_always_no(shows[0])


# -----------------------------------------------------------------------------
# Building object classification
# -----------------------------------------------------------------------------


def _first_top_atom(block: Block, key: str) -> Optional[str]:
    """Return the first top-level atom value for key, if any."""
    for stmt in top_level_stmts(block):
        if stmt.key == key and isinstance(stmt.value, Atom):
            return stmt.value.value
    return None


def classify_building_object(key: str, expanded_body: Block) -> str:
    """Classify a vanilla building-like object for Stage-4 reporting."""
    owner_type = _first_top_atom(expanded_body, "owner_type")
    capital = _first_top_atom(expanded_body, "capital")
    if key.startswith("holding_") or owner_type == "subject_holding":
        return "holding"
    if owner_type == "corporate":
        return "branch"
    if capital == "yes":
        return "capital"
    if key.startswith("building_"):
        return "regular"
    return "special"


def classify_job_object(key: str, expanded_body: Block) -> str:
    """Classify a vanilla pop job object for Stage-5 reporting."""
    category = _first_top_atom(expanded_body, "category")
    if category in {"ruler", "specialist", "worker", "complex_drone", "simple_drone"}:
        return category
    if category is None:
        return "no_category"
    return "special_other"


# -----------------------------------------------------------------------------
# Zone classification and normalization
# -----------------------------------------------------------------------------


ZONE_METADATA_KEYS = {
    "icon",
    "base_buildtime",
    "max_buildings",
    "districts_per_building",
    "max_buildings_planet_class",
    "triggered_desc",
    "swap_type",
    "swap_type_weight",
}
ZONE_AVAILABILITY_KEYS = {"potential", "unlock", "show_in_tech", "empire_limit", "planet_limit"}
ZONE_CONFIG_KEYS = {"zone_sets", "include", "exclude", "included_building_sets", "excluded_building_sets"}
ZONE_ECONOMY_KEYS = {"resources"}
ZONE_LIFECYCLE_KEYS = {"convert_to", "on_built", "on_queued", "on_unqueued"}
ZONE_AI_KEYS = {"ai_priority", "ai_resource_production", "ai_weight_coefficient"}
ZONE_TPM_KEYS = {
    "planet_modifier",
    "triggered_planet_modifier",
    "district_planet_modifier",
    "triggered_district_planet_modifier",
    "country_modifier",
    "triggered_country_modifier",
    "district_country_modifier",
    "triggered_district_country_modifier",
    "triggered_planet_pop_group_modifier_for_all",
    "triggered_planet_pop_group_modifier_for_species",
}

CANONICAL_ZONE_CATEGORIES = ["availability", "zone_config", "economy", "tpm", "lifecycle", "ai"]
ZONE_CATEGORY_DISPLAY = {
    "metadata": "METADATA",
    "availability": "AVAILABILITY",
    "zone_config": "ZONE_CONFIG",
    "economy": "ECONOMY",
    "tpm": "TPM",
    "lifecycle": "LIFECYCLE",
    "ai": "AI",
    "unknown": "UNKNOWN",
}


def zone_category_for_param(param: str) -> str:
    """Return the PIF zone object category for a top-level zone parameter."""
    if param in ZONE_METADATA_KEYS:
        return "metadata"
    if param in ZONE_AVAILABILITY_KEYS:
        return "availability"
    if param in ZONE_CONFIG_KEYS:
        return "zone_config"
    if param in ZONE_ECONOMY_KEYS:
        return "economy"
    if param in ZONE_TPM_KEYS:
        return "tpm"
    if param in ZONE_LIFECYCLE_KEYS:
        return "lifecycle"
    if param in ZONE_AI_KEYS:
        return "ai"
    return "unknown"


STATIC_TO_TRIGGERED_ZONE_MODIFIER = {
    "planet_modifier": "triggered_planet_modifier",
    "district_planet_modifier": "triggered_district_planet_modifier",
    "country_modifier": "triggered_country_modifier",
    "district_country_modifier": "triggered_district_country_modifier",
}


def normalize_zone_modifier(stmt: Stmt) -> List[Stmt]:
    """Normalize static zone modifier blocks to triggered equivalents.

    Static modifier blocks are not composable extension points.  PIF converts
    them to their triggered counterparts with ``potential = { always = yes }``
    while preserving the original modifier entries and their order.
    """
    if stmt.key not in STATIC_TO_TRIGGERED_ZONE_MODIFIER or not isinstance(stmt.value, Block):
        return [clone_node(stmt)]
    body = Block([
        Stmt("potential", "=", Block([Stmt("always", "=", Atom("yes"))])),
        *[clone_node(item) for item in stmt.value.items],
    ])
    return [Stmt(STATIC_TO_TRIGGERED_ZONE_MODIFIER[stmt.key], "=", body)]


# -----------------------------------------------------------------------------
# Zone slot classification and normalization
# -----------------------------------------------------------------------------

ZONE_SLOT_METADATA_KEYS = {"start"}
ZONE_SLOT_CONFIG_KEYS = {"include", "exclude", "included_zone_sets", "excluded_zone_sets"}
ZONE_SLOT_AVAILABILITY_KEYS = {"potential", "unlock"}

CANONICAL_ZONE_SLOT_CATEGORIES = ["zs_config", "availability"]
ZONE_SLOT_CATEGORY_DISPLAY = {
    "metadata": "METADATA",
    "zs_config": "ZS_CONFIG",
    "availability": "AVAILABILITY",
    "unknown": "UNKNOWN",
}


def zone_slot_category_for_param(param: str) -> str:
    """Return the PIF zone-slot object category for a top-level parameter."""
    if param in ZONE_SLOT_METADATA_KEYS:
        return "metadata"
    if param in ZONE_SLOT_CONFIG_KEYS:
        return "zs_config"
    if param in ZONE_SLOT_AVAILABILITY_KEYS:
        return "availability"
    return "unknown"


def normalize_zone_slot_stmt(stmt: Stmt) -> List[Stmt]:
    """Zone slots currently have no accepted statement-level normalizations."""
    return [clone_node(stmt)]


# -----------------------------------------------------------------------------
# Generic scalar helpers
# -----------------------------------------------------------------------------


NUMERIC_RE = re.compile(r"^[+-]?(?:\d+\.\d+|\d+|\.\d+)$")


def is_numeric_literal(value: str) -> bool:
    """Return True for numeric literals accepted by the PIF transformer."""
    return bool(NUMERIC_RE.match(value))


def sanitize_identifier(value: str) -> str:
    """Create a safe lowercase identifier segment for generated variable names."""
    out = re.sub(r"[^A-Za-z0-9_]+", "_", value).strip("_").lower()
    out = re.sub(r"_+", "_", out)
    return out or "value"


def make_inline_script_stmt(script: str) -> Stmt:
    return Stmt("inline_script", "=", Atom(script, quoted=True))


def resolve_atom_number(atom: Atom, variables: Dict[str, str]) -> Optional[str]:
    """Resolve a literal or ``@variable`` atom to a numeric value if possible."""
    if atom.quoted:
        return None
    if is_numeric_literal(atom.value):
        return atom.value
    if atom.value.startswith("@") and atom.value in variables and is_numeric_literal(variables[atom.value]):
        return variables[atom.value]
    return None


def replace_variables_for_compare(node: Any, variables: Dict[str, str]) -> Any:
    """Replace variable references with their resolved numeric values for validation."""
    if isinstance(node, Atom):
        resolved = resolve_atom_number(node, variables)
        return Atom(resolved, quoted=False) if resolved is not None else clone_node(node)
    if isinstance(node, Stmt):
        return Stmt(node.key, node.op, replace_variables_for_compare(node.value, variables))
    if isinstance(node, Block):
        return Block([replace_variables_for_compare(item, variables) for item in node.items])
    return clone_node(node)


def ensure_clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def relative_posix(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def count_top_params(block: Block) -> Counter[str]:
    return Counter(stmt.key for stmt in top_level_stmts(block))


# -----------------------------------------------------------------------------
# CLI helpers
# -----------------------------------------------------------------------------


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--planet", default="/mnt/data/Planet.zip", help="Path to extracted Planet directory or Planet.zip")
    parser.add_argument("--work-dir", default=None, help="Optional extraction work directory for Planet.zip")


def load_project_from_args(args: argparse.Namespace) -> StellarisProject:
    root = ensure_planet_root(Path(args.planet), Path(args.work_dir) if args.work_dir else None)
    return StellarisProject(root)

# -----------------------------------------------------------------------------
# District classification and normalization profile support
# -----------------------------------------------------------------------------

AI_KEYS = {
    "exempt_from_ai_planet_specialization",
    "ai_resource_production",
    "ai_weight",
    "ai_estimate_without_unemployment",
    "additional_ai_weight",
    "ai_weight_coefficient",
}
AVAILABILITY_KEYS = {"potential", "allow", "prerequisites", "show_tech_unlock_if"}
ECONOMIC_KEYS = {"resources"}
LIFECYCLE_KEYS = {
    "destroy_trigger",
    "on_queued",
    "on_unqueued",
    "on_built",
    "on_destroy",
    "abort_effect",
    "conversion_ratio",
    "convert_to",
}
TPM_KEYS = {
    "planet_modifier",
    "triggered_planet_modifier",
    "triggered_planet_pop_group_modifier_for_all",
    "triggered_planet_pop_group_modifier_for_species",
}
ZONE_SLOT_KEYS = {"zone_slots"}
REAL_METADATA_KEYS = {
    "base_buildtime",
    "expansion_planner",
    "default_starting_district",
    "is_uncapped",
    "inherits_capped_modifiers_from",
    "icon",
    "overlay_icon",
    "district_background",
    "custom_gui",
    "district_width",
    "has_primary_zone",
    "can_demolish",
    "show_on_uncolonized",
    "expansion_planner_type",
    "desc",
    "triggered_desc",
    "triggered_name",
    "triggered_flavor_desc",
    "icon_frame",
    "is_essential",
    "max_for_deposits_on_planet",
    "min_for_deposits_on_planet",
    "gridbox",
}
MASK_METADATA_KEYS = {"zone_slots", "potential", "show_on_uncolonized"}
MASK_KEYS = {"icon", "overlay_icon", "gridbox", "triggered_name", "triggered_flavor_desc"}

CANONICAL_REAL_CATEGORIES = ["zone_slots", "availability", "economic", "tpm", "lifecycle", "ai"]
DISTRICT_CATEGORY_DISPLAY = {
    "metadata": "METADATA",
    "zone_slots": "ZONE_SLOTS",
    "availability": "AVAILABILITY",
    "economic": "ECONOMIC",
    "tpm": "TPM",
    "lifecycle": "LIFECYCLE",
    "ai": "AI",
    "mask": "MASK",
    "unknown": "UNKNOWN",
}


def category_for_param(param: str, *, district_class: str = "real") -> str:
    """Return the PIF district object category for a top-level district parameter."""
    if district_class in {"active_mask", "sleeping_mask", "mask"}:
        if param in MASK_METADATA_KEYS:
            return "metadata"
        if param in MASK_KEYS:
            return "mask"
        return "unknown"
    if param in AI_KEYS:
        return "ai"
    if param in AVAILABILITY_KEYS:
        return "availability"
    if param in ECONOMIC_KEYS:
        return "economic"
    if param in LIFECYCLE_KEYS:
        return "lifecycle"
    if param in TPM_KEYS:
        return "tpm"
    if param in ZONE_SLOT_KEYS:
        return "zone_slots"
    if param in REAL_METADATA_KEYS:
        return "metadata"
    return "unknown"


def normalize_planet_modifier(stmt: Stmt) -> List[Stmt]:
    """Convert district planet_modifier blocks to triggered_planet_modifier.

    PIF uses triggered modifier blocks as composable extension points.  The
    unconditional vanilla form is preserved semantically through an always-yes
    potential block.
    """
    if stmt.key != "planet_modifier" or not isinstance(stmt.value, Block):
        return [clone_node(stmt)]
    body = Block([
        Stmt("potential", "=", Block([Stmt("always", "=", Atom("yes"))])),
        *[clone_node(item) for item in stmt.value.items],
    ])
    return [Stmt("triggered_planet_modifier", "=", body)]
