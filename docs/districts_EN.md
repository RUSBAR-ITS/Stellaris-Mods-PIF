# Districts — PIF Technical Specification

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

This document describes the technical organization of the `districts` layer in Planetary Infrastructure Framework. It defines how PIF analyzes vanilla districts, separates functional districts from visual district masks, assigns parameters to categories, creates PIF-owned inline scripts, extracts domain variables, and validates preservation of vanilla behavior.

## Layer overview

`districts` define the basic planetary structure. In PIF this layer matters not only as a set of buildable districts, but also as a set of visual district masks used by zones through `swap_type`.

The main technical distinction inside this layer is the separation between functional districts and district masks. Functional districts receive the full PIF schema: zone-slot structure, availability, economy, modifiers, lifecycle, and AI. Masks do not receive functional hooks because their role is visual representation of the selected zone type, not creation of a buildable object.

## Analysis methodology

### Parameter analysis

Parameters are analyzed after recursive expansion of reachable `inline_script` calls. PIF uses the actual structure of the object, not comments, assumed file purpose, or variable names. If a parameter is a modifier-carrier block, its category may be determined by the content of the block rather than only by the parameter name.

### Variable analysis

Variable domains are designed separately from parameter categories: they describe what a value controls in gameplay or balance, not where it appears in the AST. Vanilla `@variables` are resolved into concrete values and replaced by PIF-specific variables so that old global conflict points are not preserved. `value:` expressions and control-flow constants are not converted into PIF variables.

### Inline script analysis

All reachable vanilla inline scripts are classified after recursive expansion. `WHOLE` means that the script belongs to a single PIF category. `SPLIT` means that the script mixes several categories and must be distributed into PIF-owned category scripts. If a single modifier block mixes several meanings, it is not split line-by-line and is moved to the fallback category.

## Object classes

Object classes are used to choose the correct PIF schema. They are not used to change gameplay; they describe which structural hooks are safe for this kind of object.

| Class | Objects | Purpose |
| --- | --- | --- |
| real district | 58 | Functional district with the full PIF schema. |
| active district mask | 77 | Visual mask referenced by `zone.swap_type`. |
| sleeping district mask | 3 | Visual mask with mask structure and no active reference from current zones. |

## PIF layer architecture

### Object files

Each vanilla object is moved into a separate normalized PIF object file:

```txt
common/districts/pif_<vanilla_file_stem>_<district_key>.txt
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
common/inline_scripts/pif/districts/<district_key>/<category>.txt
```

A category script is the minimal conflict zone. A mod that changes only the economy of an object should not need to overwrite availability, lifecycle, or AI of the same object.

### Category order

Category script order is fixed and is part of the PIF schema:

```txt
zone_slots
availability
economic
tpm
lifecycle
ai
```

The order is required for reproducible generation, readability, and correct static validation. It must not be changed by incidental sorting.

## Parameter categories

Parameter categories define which PIF-owned inline script owns a particular part of the object. A parameter category does not have to match the variable domain.

| Category | Location | Purpose | Parameters |
| --- | --- | --- | --- |
| METADATA | Root object | Engine/UI/core fields, identity, and fields where a separate hook would add noise rather than value. | `base_buildtime`, `icon`, `overlay_icon`, planner flags, localization blocks. |
| ZONE_SLOTS | Inline script | Structural district layout. | `zone_slots`. |
| AVAILABILITY | Inline script | Conditions for existence, construction, and unlocks. | `potential`, `allow`, `prerequisites`. |
| ECONOMIC | Inline script | Economy of the district as an object. | `resources`. |
| TPM | Inline script | Planet/pop-group modifiers, jobs, and housing modifiers. | `planet_modifier`, `triggered_planet_modifier`. |
| LIFECYCLE | Inline script | District events and conversions. | `destroy_trigger`, `on_*`, `convert_to`, `conversion_ratio`. |
| AI | Inline script | AI planning for districts. | `ai_resource_production`, `additional_ai_weight`, `ai_weight_coefficient`. |
| MASK | Root object for masks | Visual layer for district masks. | `gridbox`, `triggered_name`, `triggered_flavor_desc`, icons. |

## Variable categories

| Domain file | Variables | Purpose |
| --- | --- | --- |
| `pif_districts_ai_variables.txt` | 63 | District AI planning numbers. |
| `pif_districts_building_capacity_variables.txt` | 2 | Additional building capacity from districts. |
| `pif_districts_construction_variables.txt` | 125 | District construction cost and build time. |
| `pif_districts_conversion_variables.txt` | 41 | Conversion ratios for `convert_to`. |
| `pif_districts_defense_variables.txt` | 1 | District defensive effects. |
| `pif_districts_economy_variables.txt` | 77 | District upkeep and direct production. |
| `pif_districts_housing_variables.txt` | 117 | Housing capacity from districts. |
| `pif_districts_infrastructure_effects_variables.txt` | 8 | Infrastructure effects such as building speed and decision enact speed. |
| `pif_districts_jobs_variables.txt` | 103 | Job counts added by district modifiers. |
| `pif_districts_limits_variables.txt` | 16 | Deposit-based district limits. |

Total: **10** variable files and **553** variables.

## Inline Scripts

### Inline script policy

Vanilla inline scripts are used as source material for PIF-owned category scripts. `WHOLE` means that the expanded script belongs to one category. `SPLIT` means that the expanded script must be distributed across categories. This layer has **47** reachable inline scripts: **45** `WHOLE`, **2** `SPLIT`.

### Reachable inline scripts

| Inline script | Decision | Categories | Parameters |
| --- | --- | --- | --- |
| `buildings/on_all_wilderness_buildings_districts` | `SPLIT` | `lifecycle tpm` | `on_queued on_unqueued triggered_planet_modifier` |
| `districts/ai_alloys_extra_weighting` | `WHOLE` | `ai` | `ai_resource_production` |
| `districts/ai_consumer_goods_extra_weighting` | `WHOLE` | `ai` | `ai_resource_production` |
| `districts/ai_urban_district_extra_weighting` | `WHOLE` | `ai` | `ai_resource_production` |
| `districts/district_triggered_flavor_desc_farming` | `WHOLE` | `metadata` | `triggered_flavor_desc` |
| `districts/district_triggered_flavor_desc_farming_anglers` | `WHOLE` | `metadata` | `triggered_flavor_desc` |
| `districts/district_triggered_flavor_desc_farming_default` | `WHOLE` | `metadata` | `triggered_flavor_desc` |
| `districts/district_triggered_flavor_desc_farming_exotic_gases` | `WHOLE` | `metadata` | `triggered_flavor_desc` |
| `districts/district_triggered_flavor_desc_generator` | `WHOLE` | `metadata` | `triggered_flavor_desc` |
| `districts/district_triggered_flavor_desc_generator_default` | `WHOLE` | `metadata` | `triggered_flavor_desc` |
| `districts/district_triggered_flavor_desc_generator_volatile_motes` | `WHOLE` | `metadata` | `triggered_flavor_desc` |
| `districts/district_triggered_flavor_desc_hive` | `WHOLE` | `metadata` | `triggered_flavor_desc` |
| `districts/district_triggered_flavor_desc_machine` | `WHOLE` | `metadata` | `triggered_flavor_desc` |
| `districts/district_triggered_flavor_desc_mining` | `WHOLE` | `metadata` | `triggered_flavor_desc` |
| `districts/district_triggered_flavor_desc_mining_betharian` | `WHOLE` | `metadata` | `triggered_flavor_desc` |
| `districts/district_triggered_flavor_desc_mining_default` | `WHOLE` | `metadata` | `triggered_flavor_desc` |
| `districts/district_triggered_flavor_desc_mining_rare_crystals` | `WHOLE` | `metadata` | `triggered_flavor_desc` |
| `districts/district_triggered_flavor_desc_urban` | `WHOLE` | `metadata` | `triggered_flavor_desc` |
| `districts/district_triggered_flavor_desc_urban_default` | `WHOLE` | `metadata` | `triggered_flavor_desc` |
| `districts/district_triggered_flavor_desc_urban_spiritualist` | `WHOLE` | `metadata` | `triggered_flavor_desc` |
| `districts/district_triggered_name_farming` | `WHOLE` | `metadata` | `triggered_name` |
| `districts/district_triggered_name_farming_anglers` | `WHOLE` | `metadata` | `triggered_name` |
| `districts/district_triggered_name_farming_default` | `WHOLE` | `metadata` | `triggered_name` |
| `districts/district_triggered_name_farming_exotic_gases` | `WHOLE` | `metadata` | `triggered_name` |
| `districts/district_triggered_name_generator` | `WHOLE` | `metadata` | `triggered_name` |
| `districts/district_triggered_name_generator_default` | `WHOLE` | `metadata` | `triggered_name` |
| `districts/district_triggered_name_generator_volatile_motes` | `WHOLE` | `metadata` | `triggered_name` |
| `districts/district_triggered_name_hive` | `WHOLE` | `metadata` | `triggered_name` |
| `districts/district_triggered_name_machine` | `WHOLE` | `metadata` | `triggered_name` |
| `districts/district_triggered_name_mining` | `WHOLE` | `metadata` | `triggered_name` |
| `districts/district_triggered_name_mining_betharian` | `WHOLE` | `metadata` | `triggered_name` |
| `districts/district_triggered_name_mining_default` | `WHOLE` | `metadata` | `triggered_name` |
| `districts/district_triggered_name_mining_rare_crystals` | `WHOLE` | `metadata` | `triggered_name` |
| `districts/district_triggered_name_urban` | `WHOLE` | `metadata` | `triggered_name` |
| `districts/district_triggered_name_urban_default` | `WHOLE` | `metadata` | `triggered_name` |
| `districts/district_triggered_name_urban_spiritualist` | `WHOLE` | `metadata` | `triggered_name` |
| `jobs/enforcers_add` | `WHOLE` | `tpm` | `triggered_planet_modifier` |
| `jobs/entertainers_add` | `WHOLE` | `tpm` | `triggered_planet_modifier` |
| `jobs/farmers_add` | `WHOLE` | `tpm` | `triggered_planet_modifier` |
| `jobs/habitat_miners_add` | `WHOLE` | `tpm` | `triggered_planet_modifier` |
| `jobs/habitat_researchers_add` | `WHOLE` | `tpm` | `triggered_planet_modifier` |
| `jobs/habitat_technicians_add` | `WHOLE` | `tpm` | `triggered_planet_modifier` |
| `jobs/industrial_prison_districts_factory_add` | `WHOLE` | `tpm` | `triggered_planet_modifier` |
| `jobs/industrial_prison_districts_foundry_add` | `WHOLE` | `tpm` | `triggered_planet_modifier` |
| `jobs/miners_add` | `WHOLE` | `tpm` | `triggered_planet_modifier` |
| `jobs/technicians_add` | `WHOLE` | `tpm` | `triggered_planet_modifier` |
| `jobs/thermotechnic_add` | `SPLIT` | `metadata tpm` | `triggered_desc triggered_planet_modifier` |

### Split rules

- A `WHOLE` script is moved or expanded as a single semantic block inside the matching PIF category.
- A `SPLIT` script is expanded and distributed across categories.
- An empty script may be used as no-op source material, but does not create gameplay content.
- PIF-owned category scripts are the final compatibility layer.

## Normalizations

| Normalization | Reason | Validation requirement |
| --- | --- | --- |
| `planet_modifier` -> `triggered_planet_modifier` | Allows independent extension of modifier blocks. | Unconditional trigger must be equivalent to the static vanilla modifier. |
| Vanilla `@variable` -> PIF variable | Creates object-specific tuning points instead of preserving shared vanilla variables. | Resolved PIF value must equal the original value. |
| Inline script expansion and split | Reduces conflict zones by moving content into PIF-owned category scripts. | Expanded PIF object must match expanded vanilla object after allowed normalizations. |

## Parameter order

A category defines ownership of a parameter, but it does not override ordering. The generator and validator must preserve order-sensitive sections. Repeated blocks must not be sorted automatically when order may affect selection of the first valid target, tooltip display, or final effect application.

Important areas include `zone_slots`, `convert_to`, repeated `triggered_*` blocks, and visual metadata of district masks.

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

Current result: **138 / 138 OK**, failed: **0**.

## Runtime validation

Static validation confirms structural equivalence, but runtime smoke testing is still required because the engine may depend on context that is not visible in AST comparison.

A minimal runtime check should include starting a new game, opening the planetary UI, checking regular empire, hive, machine, and corporate contexts, habitats/ringworld/ecumenopolis when possible, and reviewing `error.log` for errors related to `pif_` files.

## Layer statistics

| Metric | Value |
| --- | --- |
| Objects | 138 |
| Source files | 8 |
| Parameter names after expansion | 35 |
| Category inline scripts | 348 |
| Variable files | 10 |
| PIF variables | 553 |
| Reachable inline scripts | 47 |
| Inline scripts WHOLE | 45 |
| Inline scripts SPLIT | 2 |
| Validation checked | 138 |
| Validation OK | 138 |
| Validation failed | 0 |

## Parameter statistics

| Parameter | SUM | Real | Active mask | Sleeping mask | Category | Action |
| --- | --- | --- | --- | --- | --- | --- |
| `additional_ai_weight` | 7 | 7 | 0 | 0 | AI | Move into the corresponding PIF-owned category inline script. |
| `ai_estimate_without_unemployment` | 6 | 6 | 0 | 0 | AI | Move into the corresponding PIF-owned category inline script. |
| `ai_resource_production` | 8 | 8 | 0 | 0 | AI | Move into the corresponding PIF-owned category inline script. |
| `ai_weight_coefficient` | 8 | 8 | 0 | 0 | AI | Move into the corresponding PIF-owned category inline script. |
| `exempt_from_ai_planet_specialization` | 30 | 30 | 0 | 0 | AI | Move into the corresponding PIF-owned category inline script. |
| `allow` | 27 | 27 | 0 | 0 | AVAILABILITY | Move into the corresponding PIF-owned category inline script. |
| `potential` | 138 | 58 | 77 | 3 | class-dependent | Move according to the real-object schema; keep masks as guard or visual metadata. |
| `prerequisites` | 13 | 13 | 0 | 0 | AVAILABILITY | Move into the corresponding PIF-owned category inline script. |
| `resources` | 51 | 51 | 0 | 0 | ECONOMIC | Move into the corresponding PIF-owned category inline script. |
| `conversion_ratio` | 41 | 41 | 0 | 0 | LIFECYCLE | Move into the corresponding PIF-owned category inline script. |
| `convert_to` | 45 | 45 | 0 | 0 | LIFECYCLE | Move into the corresponding PIF-owned category inline script. |
| `destroy_trigger` | 1 | 1 | 0 | 0 | LIFECYCLE | Move into the corresponding PIF-owned category inline script. |
| `on_built` | 3 | 3 | 0 | 0 | LIFECYCLE | Move into the corresponding PIF-owned category inline script. |
| `on_queued` | 4 | 4 | 0 | 0 | LIFECYCLE | Move into the corresponding PIF-owned category inline script. |
| `on_unqueued` | 4 | 4 | 0 | 0 | LIFECYCLE | Move into the corresponding PIF-owned category inline script. |
| `base_buildtime` | 56 | 56 | 0 | 0 | METADATA | Keep in the root object. |
| `can_demolish` | 1 | 1 | 0 | 0 | METADATA | Keep in the root object. |
| `default_starting_district` | 1 | 1 | 0 | 0 | METADATA | Keep in the root object. |
| `desc` | 1 | 1 | 0 | 0 | METADATA | Keep in the root object. |
| `expansion_planner` | 12 | 12 | 0 | 0 | METADATA | Keep in the root object. |
| `expansion_planner_type` | 5 | 5 | 0 | 0 | METADATA | Keep in the root object. |
| `gridbox` | 25 | 0 | 22 | 3 | METADATA | Keep in the root object. |
| `icon` | 92 | 25 | 64 | 3 | class-dependent | Move according to the real-object schema; keep masks as guard or visual metadata. |
| `inherits_capped_modifiers_from` | 4 | 4 | 0 | 0 | METADATA | Keep in the root object. |
| `is_uncapped` | 13 | 13 | 0 | 0 | METADATA | Keep in the root object. |
| `max_for_deposits_on_planet` | 8 | 8 | 0 | 0 | METADATA | Keep in the root object. |
| `min_for_deposits_on_planet` | 8 | 8 | 0 | 0 | METADATA | Keep in the root object. |
| `overlay_icon` | 132 | 53 | 76 | 3 | class-dependent | Move according to the real-object schema; keep masks as guard or visual metadata. |
| `show_on_uncolonized` | 138 | 58 | 77 | 3 | class-dependent | Move according to the real-object schema; keep masks as guard or visual metadata. |
| `triggered_desc` | 11 | 11 | 0 | 0 | METADATA | Keep in the root object. |
| `triggered_flavor_desc` | 36 | 12 | 21 | 3 | class-dependent | Move according to the real-object schema; keep masks as guard or visual metadata. |
| `triggered_name` | 106 | 28 | 75 | 3 | class-dependent | Move according to the real-object schema; keep masks as guard or visual metadata. |
| `planet_modifier` | 46 | 46 | 0 | 0 | TPM | Normalize into triggered equivalent and then classify. |
| `triggered_planet_modifier` | 51 | 51 | 0 | 0 | TPM | Move into the corresponding PIF-owned category inline script. |
| `zone_slots` | 138 | 58 | 77 | 3 | class-dependent | Move according to the real-object schema; keep masks as guard or visual metadata. |

## Special cases and technical warnings

- District masks do not receive functional hooks for economy, lifecycle, or AI.
- Active masks are detected through actual `zone.swap_type` references.
- Localization-selection scalars such as `num_zones value > 0` remain literal.

## Affected vanilla objects

This section lists the vanilla objects overridden by PIF for this layer.

### `districts/00_special_districts.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `district_cosmogenesis_goverment` | `real` | `common/districts/pif_00_special_districts_district_cosmogenesis_goverment.txt` |
| `district_cosmogenesis_world_science` | `real` | `common/districts/pif_00_special_districts_district_cosmogenesis_world_science.txt` |
| `district_cosmogenesis_world_logic` | `real` | `common/districts/pif_00_special_districts_district_cosmogenesis_world_logic.txt` |
| `district_mindlink` | `real` | `common/districts/pif_00_special_districts_district_mindlink.txt` |

### `districts/00_urban_districts.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `district_city` | `real` | `common/districts/pif_00_urban_districts_district_city.txt` |
| `district_crashed_slaver_ship` | `real` | `common/districts/pif_00_urban_districts_district_crashed_slaver_ship.txt` |
| `district_resort` | `real` | `common/districts/pif_00_urban_districts_district_resort.txt` |
| `district_resort_1` | `real` | `common/districts/pif_00_urban_districts_district_resort_1.txt` |
| `district_resort_2` | `real` | `common/districts/pif_00_urban_districts_district_resort_2.txt` |
| `district_resort_3` | `real` | `common/districts/pif_00_urban_districts_district_resort_3.txt` |
| `district_prison` | `real` | `common/districts/pif_00_urban_districts_district_prison.txt` |
| `district_slave` | `real` | `common/districts/pif_00_urban_districts_district_slave.txt` |
| `district_hive` | `real` | `common/districts/pif_00_urban_districts_district_hive.txt` |
| `district_hive_1` | `real` | `common/districts/pif_00_urban_districts_district_hive_1.txt` |
| `district_hive_2` | `real` | `common/districts/pif_00_urban_districts_district_hive_2.txt` |
| `district_hive_3` | `real` | `common/districts/pif_00_urban_districts_district_hive_3.txt` |
| `district_nexus` | `real` | `common/districts/pif_00_urban_districts_district_nexus.txt` |
| `district_nexus_1` | `real` | `common/districts/pif_00_urban_districts_district_nexus_1.txt` |
| `district_nexus_2` | `real` | `common/districts/pif_00_urban_districts_district_nexus_2.txt` |
| `district_nexus_3` | `real` | `common/districts/pif_00_urban_districts_district_nexus_3.txt` |
| `district_prison_industrial` | `real` | `common/districts/pif_00_urban_districts_district_prison_industrial.txt` |
| `district_battle_thrall` | `real` | `common/districts/pif_00_urban_districts_district_battle_thrall.txt` |
| `district_srw_commercial` | `real` | `common/districts/pif_00_urban_districts_district_srw_commercial.txt` |

### `districts/01_arcology_districts.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `district_arcology_housing` | `real` | `common/districts/pif_01_arcology_districts_district_arcology_housing.txt` |
| `district_arcology_leisure` | `real` | `common/districts/pif_01_arcology_districts_district_arcology_leisure.txt` |
| `district_arcology_urban_1` | `real` | `common/districts/pif_01_arcology_districts_district_arcology_urban_1.txt` |
| `district_arcology_urban_2` | `real` | `common/districts/pif_01_arcology_districts_district_arcology_urban_2.txt` |
| `district_arcology_urban_3` | `real` | `common/districts/pif_01_arcology_districts_district_arcology_urban_3.txt` |

### `districts/02_rural_districts.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `district_generator` | `real` | `common/districts/pif_02_rural_districts_district_generator.txt` |
| `district_generator_uncapped` | `real` | `common/districts/pif_02_rural_districts_district_generator_uncapped.txt` |
| `district_mining` | `real` | `common/districts/pif_02_rural_districts_district_mining.txt` |
| `district_mining_uncapped` | `real` | `common/districts/pif_02_rural_districts_district_mining_uncapped.txt` |
| `district_farming` | `real` | `common/districts/pif_02_rural_districts_district_farming.txt` |
| `district_farming_uncapped` | `real` | `common/districts/pif_02_rural_districts_district_farming_uncapped.txt` |
| `district_geothermal` | `real` | `common/districts/pif_02_rural_districts_district_geothermal.txt` |
| `district_melting` | `real` | `common/districts/pif_02_rural_districts_district_melting.txt` |
| `district_polytechnic` | `real` | `common/districts/pif_02_rural_districts_district_polytechnic.txt` |

### `districts/03_habitat_districts.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `district_hab_housing` | `real` | `common/districts/pif_03_habitat_districts_district_hab_housing.txt` |
| `district_hab_energy` | `real` | `common/districts/pif_03_habitat_districts_district_hab_energy.txt` |
| `district_hab_mining` | `real` | `common/districts/pif_03_habitat_districts_district_hab_mining.txt` |
| `district_hab_science` | `real` | `common/districts/pif_03_habitat_districts_district_hab_science.txt` |

### `districts/04_ringworld_districts.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `district_rw_city` | `real` | `common/districts/pif_04_ringworld_districts_district_rw_city.txt` |
| `district_rw_hive` | `real` | `common/districts/pif_04_ringworld_districts_district_rw_hive.txt` |
| `district_rw_nexus` | `real` | `common/districts/pif_04_ringworld_districts_district_rw_nexus.txt` |
| `district_rw_generator` | `real` | `common/districts/pif_04_ringworld_districts_district_rw_generator.txt` |
| `district_rw_commercial` | `real` | `common/districts/pif_04_ringworld_districts_district_rw_commercial.txt` |
| `district_rw_science` | `real` | `common/districts/pif_04_ringworld_districts_district_rw_science.txt` |
| `district_rw_farming` | `real` | `common/districts/pif_04_ringworld_districts_district_rw_farming.txt` |
| `district_rw_urban_1` | `real` | `common/districts/pif_04_ringworld_districts_district_rw_urban_1.txt` |
| `district_rw_urban_2` | `real` | `common/districts/pif_04_ringworld_districts_district_rw_urban_2.txt` |
| `district_rw_urban_3` | `real` | `common/districts/pif_04_ringworld_districts_district_rw_urban_3.txt` |

### `districts/05_wilderness_districts.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `district_craglands` | `real` | `common/districts/pif_05_wilderness_districts_district_craglands.txt` |
| `district_photosynthesis_fields` | `real` | `common/districts/pif_05_wilderness_districts_district_photosynthesis_fields.txt` |
| `district_photosynthesis_fields_uncapped` | `real` | `common/districts/pif_05_wilderness_districts_district_photosynthesis_fields_uncapped.txt` |
| `district_hollow_mountains` | `real` | `common/districts/pif_05_wilderness_districts_district_hollow_mountains.txt` |
| `district_hollow_mountains_uncapped` | `real` | `common/districts/pif_05_wilderness_districts_district_hollow_mountains_uncapped.txt` |
| `district_orchard_forests` | `real` | `common/districts/pif_05_wilderness_districts_district_orchard_forests.txt` |
| `district_orchard_forests_uncapped` | `real` | `common/districts/pif_05_wilderness_districts_district_orchard_forests_uncapped.txt` |

### `districts/06_swap_districts.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `district_mining_rare_crystals` | `active_mask` | `common/districts/pif_06_swap_districts_district_mining_rare_crystals.txt` |
| `district_mining_betharian` | `active_mask` | `common/districts/pif_06_swap_districts_district_mining_betharian.txt` |
| `district_mining_engineering` | `sleeping_mask` | `common/districts/pif_06_swap_districts_district_mining_engineering.txt` |
| `district_mining_physics` | `active_mask` | `common/districts/pif_06_swap_districts_district_mining_physics.txt` |
| `district_generator_volatile_motes` | `active_mask` | `common/districts/pif_06_swap_districts_district_generator_volatile_motes.txt` |
| `district_generator_physics` | `sleeping_mask` | `common/districts/pif_06_swap_districts_district_generator_physics.txt` |
| `district_farming_exotic_gases` | `active_mask` | `common/districts/pif_06_swap_districts_district_farming_exotic_gases.txt` |
| `district_farming_society` | `sleeping_mask` | `common/districts/pif_06_swap_districts_district_farming_society.txt` |
| `district_orders_demesne` | `active_mask` | `common/districts/pif_06_swap_districts_district_orders_demesne.txt` |
| `district_hab_mining_rare_crystals` | `active_mask` | `common/districts/pif_06_swap_districts_district_hab_mining_rare_crystals.txt` |
| `district_hab_energy_volatile_motes` | `active_mask` | `common/districts/pif_06_swap_districts_district_hab_energy_volatile_motes.txt` |
| `district_hab_energy_exotic_gases` | `active_mask` | `common/districts/pif_06_swap_districts_district_hab_energy_exotic_gases.txt` |
| `district_arcology_mixed_industry` | `active_mask` | `common/districts/pif_06_swap_districts_district_arcology_mixed_industry.txt` |
| `district_arcology_arms_industry` | `active_mask` | `common/districts/pif_06_swap_districts_district_arcology_arms_industry.txt` |
| `district_arcology_civilian_industry` | `active_mask` | `common/districts/pif_06_swap_districts_district_arcology_civilian_industry.txt` |
| `district_arcology_research` | `active_mask` | `common/districts/pif_06_swap_districts_district_arcology_research.txt` |
| `district_arcology_research_physics` | `active_mask` | `common/districts/pif_06_swap_districts_district_arcology_research_physics.txt` |
| `district_arcology_research_society` | `active_mask` | `common/districts/pif_06_swap_districts_district_arcology_research_society.txt` |
| `district_arcology_research_engineering` | `active_mask` | `common/districts/pif_06_swap_districts_district_arcology_research_engineering.txt` |
| `district_arcology_administrative` | `active_mask` | `common/districts/pif_06_swap_districts_district_arcology_administrative.txt` |
| `district_arcology_spiritualist` | `active_mask` | `common/districts/pif_06_swap_districts_district_arcology_spiritualist.txt` |
| `district_arcology_organic_housing` | `active_mask` | `common/districts/pif_06_swap_districts_district_arcology_organic_housing.txt` |
| `district_arcology_fortress` | `active_mask` | `common/districts/pif_06_swap_districts_district_arcology_fortress.txt` |
| `district_arcology_trade` | `active_mask` | `common/districts/pif_06_swap_districts_district_arcology_trade.txt` |
| `district_ring_world_industrial` | `active_mask` | `common/districts/pif_06_swap_districts_district_ring_world_industrial.txt` |
| `district_ring_world_foundry` | `active_mask` | `common/districts/pif_06_swap_districts_district_ring_world_foundry.txt` |
| `district_ring_world_factory` | `active_mask` | `common/districts/pif_06_swap_districts_district_ring_world_factory.txt` |
| `district_ring_world_research` | `active_mask` | `common/districts/pif_06_swap_districts_district_ring_world_research.txt` |
| `district_ring_world_research_physics` | `active_mask` | `common/districts/pif_06_swap_districts_district_ring_world_research_physics.txt` |
| `district_ring_world_research_society` | `active_mask` | `common/districts/pif_06_swap_districts_district_ring_world_research_society.txt` |
| `district_ring_world_research_engineering` | `active_mask` | `common/districts/pif_06_swap_districts_district_ring_world_research_engineering.txt` |
| `district_ring_world_administrative` | `active_mask` | `common/districts/pif_06_swap_districts_district_ring_world_administrative.txt` |
| `district_ring_world_spiritualist` | `active_mask` | `common/districts/pif_06_swap_districts_district_ring_world_spiritualist.txt` |
| `district_ring_world_organic_housing` | `active_mask` | `common/districts/pif_06_swap_districts_district_ring_world_organic_housing.txt` |
| `district_ring_world_fortress` | `active_mask` | `common/districts/pif_06_swap_districts_district_ring_world_fortress.txt` |
| `district_ring_world_trade` | `active_mask` | `common/districts/pif_06_swap_districts_district_ring_world_trade.txt` |
| `district_ring_world_food` | `active_mask` | `common/districts/pif_06_swap_districts_district_ring_world_food.txt` |
| `district_ring_world_energy` | `active_mask` | `common/districts/pif_06_swap_districts_district_ring_world_energy.txt` |
| `district_nexus_industrial` | `active_mask` | `common/districts/pif_06_swap_districts_district_nexus_industrial.txt` |
| `district_nexus_foundry` | `active_mask` | `common/districts/pif_06_swap_districts_district_nexus_foundry.txt` |
| `district_nexus_factory` | `active_mask` | `common/districts/pif_06_swap_districts_district_nexus_factory.txt` |
| `district_nexus_research` | `active_mask` | `common/districts/pif_06_swap_districts_district_nexus_research.txt` |
| `district_nexus_research_physics` | `active_mask` | `common/districts/pif_06_swap_districts_district_nexus_research_physics.txt` |
| `district_nexus_research_society` | `active_mask` | `common/districts/pif_06_swap_districts_district_nexus_research_society.txt` |
| `district_nexus_research_engineering` | `active_mask` | `common/districts/pif_06_swap_districts_district_nexus_research_engineering.txt` |
| `district_nexus_administrative` | `active_mask` | `common/districts/pif_06_swap_districts_district_nexus_administrative.txt` |
| `district_nexus_spiritualist` | `active_mask` | `common/districts/pif_06_swap_districts_district_nexus_spiritualist.txt` |
| `district_nexus_organic_housing` | `active_mask` | `common/districts/pif_06_swap_districts_district_nexus_organic_housing.txt` |
| `district_nexus_fortress` | `active_mask` | `common/districts/pif_06_swap_districts_district_nexus_fortress.txt` |
| `district_nexus_trade` | `active_mask` | `common/districts/pif_06_swap_districts_district_nexus_trade.txt` |
| `district_nexus_mining` | `active_mask` | `common/districts/pif_06_swap_districts_district_nexus_mining.txt` |
| `district_nexus_betharian` | `active_mask` | `common/districts/pif_06_swap_districts_district_nexus_betharian.txt` |
| `district_nexus_rare_crystals` | `active_mask` | `common/districts/pif_06_swap_districts_district_nexus_rare_crystals.txt` |
| `district_nexus_energy` | `active_mask` | `common/districts/pif_06_swap_districts_district_nexus_energy.txt` |
| `district_nexus_volatile_motes` | `active_mask` | `common/districts/pif_06_swap_districts_district_nexus_volatile_motes.txt` |
| `district_nexus_exotic_gases` | `active_mask` | `common/districts/pif_06_swap_districts_district_nexus_exotic_gases.txt` |
| `district_hive_industrial` | `active_mask` | `common/districts/pif_06_swap_districts_district_hive_industrial.txt` |
| `district_hive_foundry` | `active_mask` | `common/districts/pif_06_swap_districts_district_hive_foundry.txt` |
| `district_hive_factory` | `active_mask` | `common/districts/pif_06_swap_districts_district_hive_factory.txt` |
| `district_hive_research` | `active_mask` | `common/districts/pif_06_swap_districts_district_hive_research.txt` |
| `district_hive_research_physics` | `active_mask` | `common/districts/pif_06_swap_districts_district_hive_research_physics.txt` |
| `district_hive_research_society` | `active_mask` | `common/districts/pif_06_swap_districts_district_hive_research_society.txt` |
| `district_hive_research_engineering` | `active_mask` | `common/districts/pif_06_swap_districts_district_hive_research_engineering.txt` |
| `district_hive_administrative` | `active_mask` | `common/districts/pif_06_swap_districts_district_hive_administrative.txt` |
| `district_hive_fortress` | `active_mask` | `common/districts/pif_06_swap_districts_district_hive_fortress.txt` |
| `district_hive_trade` | `active_mask` | `common/districts/pif_06_swap_districts_district_hive_trade.txt` |
| `district_hive_food` | `active_mask` | `common/districts/pif_06_swap_districts_district_hive_food.txt` |
| `district_hive_exotic_gases` | `active_mask` | `common/districts/pif_06_swap_districts_district_hive_exotic_gases.txt` |
| `district_hive_mining` | `active_mask` | `common/districts/pif_06_swap_districts_district_hive_mining.txt` |
| `district_betharian_hive` | `active_mask` | `common/districts/pif_06_swap_districts_district_betharian_hive.txt` |
| `district_rare_crystals_hive` | `active_mask` | `common/districts/pif_06_swap_districts_district_rare_crystals_hive.txt` |
| `district_hive_energy` | `active_mask` | `common/districts/pif_06_swap_districts_district_hive_energy.txt` |
| `district_hive_volatile_motes` | `active_mask` | `common/districts/pif_06_swap_districts_district_hive_volatile_motes.txt` |
| `district_hive_spawning` | `active_mask` | `common/districts/pif_06_swap_districts_district_hive_spawning.txt` |
| `district_resort_zoo` | `active_mask` | `common/districts/pif_06_swap_districts_district_resort_zoo.txt` |
| `district_resort_museum` | `active_mask` | `common/districts/pif_06_swap_districts_district_resort_museum.txt` |
| `district_resort_hunting_ground` | `active_mask` | `common/districts/pif_06_swap_districts_district_resort_hunting_ground.txt` |
| `district_resort_spiritual_retreat` | `active_mask` | `common/districts/pif_06_swap_districts_district_resort_spiritual_retreat.txt` |
| `district_resort_restoration_enclave` | `active_mask` | `common/districts/pif_06_swap_districts_district_resort_restoration_enclave.txt` |
| `district_resort_proving_grounds` | `active_mask` | `common/districts/pif_06_swap_districts_district_resort_proving_grounds.txt` |

## Source files and documentation used

| Type | Files |
| --- | --- |
| Vanilla object files | `common/districts/*.txt` |
| Inline scripts | reachable files under `common/inline_scripts/` |
| Scripted variables | `common/scripted_variables/*.txt` |
| Object documentation | `common/districts/00_DOCUMENTATION.txt` |
| Generated reports | `Analytics/reports/districts/` |
