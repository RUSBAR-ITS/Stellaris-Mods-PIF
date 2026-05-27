# Zone Slots — PIF Technical Specification

## Table of Contents

- [Document purpose](#document-purpose)
- [Layer overview](#layer-overview)
- [Analysis methodology](#analysis-methodology)
  - [Parameter analysis](#parameter-analysis)
  - [Variable analysis](#variable-analysis)
  - [Inline script analysis](#inline-script-analysis)
- [Object classes](#object-classes)
- [PIF layer architecture](#pif-layer-architecture)
  - [Object files](#object-files)
  - [Root object](#root-object)
  - [Category inline scripts](#category-inline-scripts)
  - [Category order](#category-order)
- [Parameter categories](#parameter-categories)
- [Variable categories](#variable-categories)
- [Inline Scripts](#inline-scripts)
  - [Inline script policy](#inline-script-policy)
  - [Reachable inline scripts](#reachable-inline-scripts)
  - [Split rules](#split-rules)
- [Normalizations](#normalizations)
- [Parameter order](#parameter-order)
- [Static validation](#static-validation)
- [Runtime validation](#runtime-validation)
- [Layer statistics](#layer-statistics)
- [Parameter statistics](#parameter-statistics)
- [Special cases and technical warnings](#special-cases-and-technical-warnings)
- [Affected vanilla objects](#affected-vanilla-objects)
- [Source files and documentation used](#source-files-and-documentation-used)

## Document purpose

This document describes the technical organization of the `zone_slots` layer in Planetary Infrastructure Framework. It defines how PIF analyzes zone slots, preserves their structural role inside districts, separates configuration and availability categories, creates PIF-owned inline scripts, and validates preservation of vanilla behavior.

## Layer overview

`zone_slots` describe which zones may exist inside a district. This is the smallest planetary infrastructure layer, but it is critical for preserving district layout structure.

The layer contains almost no balance numbers and does not use reachable vanilla inline scripts. PIF therefore keeps it as a lightweight object-per-file schema with two categories: slot configuration and availability.

## Analysis methodology

### Parameter analysis

Parameters are analyzed after recursive expansion of reachable `inline_script` calls. PIF uses the actual structure of the object, not comments, assumed file purpose, or variable names. If a parameter is a modifier-carrier block, its category may be determined by the content of the block rather than only by the parameter name.

### Variable analysis

No meaningful variables are extracted for this layer, but that absence is the result of analysis rather than an assumption. Vanilla `@variables` are resolved into concrete values and replaced by PIF-specific variables so that old global conflict points are not preserved. `value:` expressions and control-flow constants are not converted into PIF variables.

### Inline script analysis

All reachable vanilla inline scripts are classified after recursive expansion. `WHOLE` means that the script belongs to a single PIF category. `SPLIT` means that the script mixes several categories and must be distributed into PIF-owned category scripts. If a single modifier block mixes several meanings, it is not split line-by-line and is moved to the fallback category.

## Object classes

Object classes are used to choose the correct PIF schema. They are not used to change gameplay; they describe which structural hooks are safe for this kind of object.

| Class | Objects | Purpose |
| --- | --- | --- |
| zone slot | 27 | The only object class. All slots receive the same PIF schema. |

## PIF layer architecture

### Object files

Each vanilla object is moved into a separate normalized PIF object file:

```txt
common/zone_slots/pif_<vanilla_file_stem>_<zone_slot_key>.txt
```

Rules:

- one top-level object per file;
- the file name preserves origin through `vanilla_file_stem`;
- the object key is included in the file name so the path is unambiguous;
- the root object contains metadata and `inline_script` calls to PIF-owned category scripts.

### Root object

The root object contains parameters that must remain close to object identity, UI, or engine-sensitive structure. These fields are not moved into a separate category script when a separate hook would not provide useful compatibility or could create a false extension point.

The root object also contains calls to PIF-owned inline scripts in fixed category order.

### Category inline scripts

Each functional category is placed into its own PIF-owned inline script:

```txt
common/inline_scripts/pif/zone_slots/<zone_slot_key>/<category>.txt
```

A category script is the minimal conflict zone. A mod that changes only the economy of an object should not need to overwrite availability, lifecycle, or AI of the same object.

### Category order

Category script order is fixed and is part of the PIF schema:

```txt
zs_config
availability
```

The order is required for reproducible generation, readability, and correct static validation. It must not be changed by incidental sorting.

## Parameter categories

Parameter categories define which PIF-owned inline script owns a particular part of the object. A parameter category does not have to match the variable domain.

| Category | Location | Purpose | Parameters |
| --- | --- | --- | --- |
| METADATA | Root object | Core slot metadata. | `start`. |
| ZS_CONFIG | Inline script | Zone filters and zone sets allowed by the slot. | `include`, `exclude`, `included_zone_sets`, `excluded_zone_sets`. |
| AVAILABILITY | Inline script | Slot existence and unlock conditions. | `potential`, `unlock`. |

## Variable categories

No meaningful variable domains are extracted for this layer. Vanilla objects do not contain meaningful tuning scalars that require PIF scripted variables.

## Inline Scripts

### Inline script policy

Vanilla inline scripts are used as source material for PIF-owned category scripts. `WHOLE` means that the expanded script belongs to one category. `SPLIT` means that the expanded script must be distributed across categories. This layer has **0** reachable inline scripts: **0** `WHOLE`, **0** `SPLIT`.

### Reachable inline scripts

No reachable vanilla inline scripts were found.

### Split rules

- A `WHOLE` script is moved or expanded as a single semantic block inside the matching PIF category.
- A `SPLIT` script is expanded and distributed across categories.
- An empty script may be used as no-op source material, but does not create gameplay content.
- PIF-owned category scripts are the final compatibility layer.

## Normalizations

| Normalization | Reason | Validation requirement |
| --- | --- | --- |
| Inline script policy | No reachable vanilla inline scripts are used by this layer. | Generated PIF scripts are structural extension points. |

## Parameter order

A category defines ownership of a parameter, but it does not override ordering. The generator and validator must preserve order-sensitive sections. Repeated blocks must not be sorted automatically when order may affect selection of the first valid target, tooltip display, or final effect application.

Important areas include `start`, include/exclude filters, and preservation of service slots.

## Static validation

Validation compares expanded vanilla objects with expanded PIF objects after applying explicitly allowed normalizations.

The checks cover:

- presence of all expected objects;
- absence of extra generated objects;
- resolved inline scripts;
- resolved PIF variables;
- no duplicate or missing variables;
- matching expanded category content;
- preserved order-sensitive sections;
- warning-level special cases without turning vanilla peculiarities into hard failures.

Current result: **27 / 27 OK**, failed: **0**.

## Runtime validation

Static validation confirms structural equivalence, but runtime smoke testing is still required because the engine may depend on context that is not visible in AST comparison.

A minimal runtime check should include starting a new game, opening the planetary UI, checking regular empire, hive, machine, and corporate contexts, habitats/ringworld/ecumenopolis when possible, and reviewing `error.log` for errors related to `pif_` files.

## Layer statistics

| Metric | Value |
| --- | --- |
| Objects | 27 |
| Source files | 2 |
| Parameter names after expansion | 6 |
| Category inline scripts | 54 |
| Variable files | 0 |
| PIF variables | 0 |
| Reachable inline scripts | 0 |
| Inline scripts WHOLE | 0 |
| Inline scripts SPLIT | 0 |
| Validation checked | 27 |
| Validation OK | 27 |
| Validation failed | 0 |

## Parameter statistics

| Parameter | Objects | Category | Action |
| --- | --- | --- | --- |
| `potential` | 3 | AVAILABILITY | Move into the corresponding PIF-owned category inline script. |
| `unlock` | 27 | AVAILABILITY | Move into the corresponding PIF-owned category inline script. |
| `start` | 2 | METADATA | Keep in the root object. |
| `exclude` | 1 | ZS_CONFIG | Move into the corresponding PIF-owned category inline script. |
| `include` | 1 | ZS_CONFIG | Move into the corresponding PIF-owned category inline script. |
| `included_zone_sets` | 26 | ZS_CONFIG | Move into the corresponding PIF-owned category inline script. |

## Special cases and technical warnings

- `slot_city_05` is preserved even if it is not used by current districts.
- `slot_empty` is preserved as a service slot for district masks.
- The `slot_city_government` and `zone_default` peculiarity is not automatically corrected because PIF preserves vanilla behavior.

## Affected vanilla objects

This section lists the vanilla objects overridden by PIF for this layer.

### `zone_slots/00_zone_slots.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `slot_city_government` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_city_government.txt` |
| `slot_city_01` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_city_01.txt` |
| `slot_city_02` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_city_02.txt` |
| `slot_minerals` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_minerals.txt` |
| `slot_energy` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_energy.txt` |
| `slot_food` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_food.txt` |
| `slot_city_04` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_city_04.txt` |
| `slot_city_05` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_city_05.txt` |
| `slot_rw_urban_01` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_rw_urban_01.txt` |
| `slot_rw_urban_02` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_rw_urban_02.txt` |
| `slot_rw_urban_03` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_rw_urban_03.txt` |
| `slot_arcology_urban_01` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_arcology_urban_01.txt` |
| `slot_arcology_urban_02` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_arcology_urban_02.txt` |
| `slot_arcology_urban_03` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_arcology_urban_03.txt` |
| `slot_nexus` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_nexus.txt` |
| `slot_hive` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_hive.txt` |
| `slot_cosmogenesis_government` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_cosmogenesis_government.txt` |
| `slot_empty` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_empty.txt` |
| `slot_resort_01` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_resort_01.txt` |
| `slot_resort_02` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_resort_02.txt` |
| `slot_resort_attraction_01` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_resort_attraction_01.txt` |
| `slot_polytechnic` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_polytechnic.txt` |

### `zone_slots/01_habitat_zone_slots.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `slot_habitat_01` | `zone_slot` | `common/zone_slots/pif_01_habitat_zone_slots_slot_habitat_01.txt` |
| `slot_habitat_02` | `zone_slot` | `common/zone_slots/pif_01_habitat_zone_slots_slot_habitat_02.txt` |
| `slot_habitat_energy` | `zone_slot` | `common/zone_slots/pif_01_habitat_zone_slots_slot_habitat_energy.txt` |
| `slot_habitat_minerals` | `zone_slot` | `common/zone_slots/pif_01_habitat_zone_slots_slot_habitat_minerals.txt` |
| `slot_habitat_research` | `zone_slot` | `common/zone_slots/pif_01_habitat_zone_slots_slot_habitat_research.txt` |

## Source files and documentation used

| Type | Files |
| --- | --- |
| Vanilla object files | `common/zone_slots/*.txt` |
| Inline scripts | reachable files under `common/inline_scripts/` |
| Scripted variables | `common/scripted_variables/*.txt` |
| Object documentation | `common/zone_slots/99_HOW_TO_ZONE.txt` |
| Generated reports | `Analytics/reports/zone_slots/` |
