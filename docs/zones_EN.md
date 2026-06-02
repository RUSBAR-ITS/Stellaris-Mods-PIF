# Zones — PIF Technical Specification

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

This document describes the technical organization of the `zones` layer in Planetary Infrastructure Framework. It defines how PIF analyzes zones, preserves their role as the bridge between districts, zone slots, and buildings, assigns parameters to categories, creates PIF-owned inline scripts, extracts domain variables, and validates preservation of vanilla behavior.

## Layer overview

`zones` are the connector layer of planetary infrastructure. They define which building sets are allowed in a zone, which zone sets are assigned, which district masks are used for visual swap display, and which planet or district effects are attached to the zone.

For PIF this layer is an important compatibility boundary between districts and buildings. Zones cannot be treated as a simple list of building filters: they participate in display, limits, AI, and conditional modifiers.

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
| zone | 120 | The only object class. All zones receive the same PIF schema. |

## PIF layer architecture

### Object files

Each vanilla object is moved into a separate normalized PIF object file:

```txt
common/zones/pif_<vanilla_file_stem>_<zone_key>.txt
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
common/inline_scripts/pif/zones/<zone_key>/<category>.txt
```

A category script is the minimal conflict zone. A mod that changes only the economy of an object should not need to overwrite availability, lifecycle, or AI of the same object.

### Category order

Category script order is fixed and is part of the PIF schema:

```txt
availability
zone_config
economy
tpm
lifecycle
ai
```

The order is required for reproducible generation, readability, and correct static validation. It must not be changed by incidental sorting.

## Parameter categories

Parameter categories define which PIF-owned inline script owns a particular part of the object. A parameter category does not have to match the variable domain.

| Category | Location | Purpose | Parameters |
| --- | --- | --- | --- |
| METADATA | Root object | Core/UI fields and swap metadata. | `icon`, `base_buildtime`, `swap_type`, `swap_type_weight`, capacity fields. |
| AVAILABILITY | Inline script | Zone existence, unlock, and limit conditions. | `potential`, `unlock`, `planet_limit`. |
| ZONE_CONFIG | Inline script | Zone sets and building filters. | `zone_sets`, `include`, `included_building_sets`, `excluded_building_sets`. |
| ECONOMY | Inline script | Zone economic block. | `resources`. |
| TPM | Inline script | Planet/district/country modifiers of the zone. | `planet_modifier`, `triggered_district_planet_modifier`, etc. |
| LIFECYCLE | Inline script | Zone conversions. | `convert_to`. |
| AI | Inline script | AI planning for zones. | `ai_priority`, `ai_resource_production`, `ai_weight_coefficient`. |

## Variable categories

| Domain file | Variables | Purpose |
| --- | --- | --- |
| `pif_zones_ai_variables.txt` | 171 | Zone AI weights and resource hints. |
| `pif_zones_building_capacity_variables.txt` | 120 | Building capacity and max buildings from zones. `zone_building_slots_add` uses the same variables as `max_buildings`. |
| `pif_zones_construction_variables.txt` | 236 | Zone build time and construction-related values. |
| `pif_zones_economy_variables.txt` | 0 | Reserved economy domain; no variables in current data. |
| `pif_zones_housing_variables.txt` | 96 | Housing effects from zone modifiers. |
| `pif_zones_jobs_defense_variables.txt` | 31 | Defensive jobs and modifiers. |
| `pif_zones_jobs_industry_variables.txt` | 82 | Industrial job slots and production job modifiers. |
| `pif_zones_jobs_research_variables.txt` | 292 | Research job slots and research-related values. |
| `pif_zones_jobs_resource_extraction_variables.txt` | 158 | Resource extraction job slots. |
| `pif_zones_jobs_services_variables.txt` | 72 | Service and amenity job slots. |
| `pif_zones_jobs_trade_variables.txt` | 54 | Trade job slots. |
| `pif_zones_jobs_unity_admin_variables.txt` | 182 | Unity and administration job slots. |
| `pif_zones_limits_variables.txt` | 13 | Zone limits and cap-related values. |
| `pif_zones_planet_output_modifiers_variables.txt` | 37 | Planet output modifiers coming from zones. |

Total: **14** variable files and **1544** variables.

## Inline Scripts

### Inline script policy

Vanilla inline scripts are used as source material for PIF-owned category scripts. `WHOLE` means that the expanded script belongs to one category. `SPLIT` means that the expanded script must be distributed across categories. This layer has **39** reachable inline scripts: **19** `WHOLE`, **20** `SPLIT`.

### Reachable inline scripts

| Inline script | Decision | Categories | Parameters |
| --- | --- | --- | --- |
| `jobs/zone_biologists_add` | `WHOLE` | `tpm` | `triggered_district_planet_modifier` |
| `jobs/zone_engineers_add` | `WHOLE` | `tpm` | `triggered_district_planet_modifier` |
| `jobs/zone_entertainers_add` | `WHOLE` | `tpm` | `triggered_district_planet_modifier` |
| `jobs/zone_factory_add` | `WHOLE` | `tpm` | `triggered_district_planet_modifier` |
| `jobs/zone_farmers_add` | `WHOLE` | `tpm` | `triggered_district_planet_modifier` |
| `jobs/zone_foundry_add` | `WHOLE` | `tpm` | `triggered_district_planet_modifier` |
| `jobs/zone_healthcare_jobs_add` | `WHOLE` | `tpm` | `triggered_district_planet_modifier` |
| `jobs/zone_miner_add` | `WHOLE` | `tpm` | `triggered_district_planet_modifier` |
| `jobs/zone_physicists_add` | `WHOLE` | `tpm` | `triggered_district_planet_modifier` |
| `jobs/zone_researchers_add` | `WHOLE` | `tpm` | `triggered_district_planet_modifier` |
| `jobs/zone_resort_worker_add` | `WHOLE` | `tpm` | `triggered_district_planet_modifier` |
| `jobs/zone_soldiers_add` | `WHOLE` | `tpm` | `triggered_district_planet_modifier` |
| `jobs/zone_technicians_add` | `WHOLE` | `tpm` | `triggered_district_planet_modifier` |
| `jobs/zone_trader_add` | `WHOLE` | `tpm` | `triggered_district_planet_modifier` |
| `jobs/zone_unity_jobs_add` | `WHOLE` | `tpm` | `triggered_district_planet_modifier` |
| `zones/shared_arcology_zone_modifiers` | `WHOLE` | `tpm` | `triggered_district_planet_modifier` |
| `zones/shared_betharian_zone` | `SPLIT` | `ai availability economy lifecycle metadata tpm zone_config` | `ai_priority base_buildtime convert_to icon included_building_sets planet_modifier potential resources triggered_district_planet_modifier unlock` |
| `zones/shared_city_non_urban_zone_modifiers` | `WHOLE` | `tpm` | `triggered_district_planet_modifier` |
| `zones/shared_energy_zone` | `SPLIT` | `ai availability economy lifecycle metadata tpm zone_config` | `ai_priority base_buildtime convert_to icon included_building_sets planet_modifier potential resources triggered_district_planet_modifier unlock` |
| `zones/shared_exotic_gases_zone` | `SPLIT` | `ai availability economy lifecycle metadata tpm zone_config` | `ai_priority base_buildtime convert_to icon included_building_sets planet_modifier potential resources triggered_desc triggered_district_planet_modifier unlock` |
| `zones/shared_food_zone` | `SPLIT` | `ai availability economy lifecycle metadata tpm zone_config` | `ai_priority base_buildtime convert_to icon included_building_sets planet_modifier potential resources triggered_district_planet_modifier unlock` |
| `zones/shared_fortress_zone` | `SPLIT` | `ai availability economy metadata tpm zone_config` | `ai_priority base_buildtime icon included_building_sets planet_modifier potential resources triggered_district_planet_modifier unlock` |
| `zones/shared_industrial_factory_zone` | `SPLIT` | `ai availability economy metadata tpm zone_config` | `ai_priority ai_resource_production base_buildtime icon included_building_sets planet_modifier potential resources triggered_district_planet_modifier unlock` |
| `zones/shared_industrial_foundry_zone` | `SPLIT` | `ai availability economy metadata tpm zone_config` | `ai_priority ai_resource_production ai_weight_coefficient base_buildtime icon included_building_sets planet_modifier potential resources triggered_district_planet_modifier unlock` |
| `zones/shared_industrial_zone` | `SPLIT` | `ai availability economy metadata tpm zone_config` | `ai_priority ai_resource_production ai_weight_coefficient base_buildtime icon included_building_sets planet_modifier potential resources triggered_district_planet_modifier unlock` |
| `zones/shared_minerals_zone` | `SPLIT` | `ai availability economy lifecycle metadata tpm zone_config` | `ai_priority base_buildtime convert_to icon included_building_sets planet_modifier potential resources triggered_district_planet_modifier unlock` |
| `zones/shared_rare_crystals_zone` | `SPLIT` | `ai availability economy lifecycle metadata tpm zone_config` | `ai_priority base_buildtime convert_to icon included_building_sets planet_modifier potential resources triggered_desc triggered_district_planet_modifier unlock` |
| `zones/shared_research_engineering_zone` | `SPLIT` | `availability economy metadata tpm zone_config` | `base_buildtime icon included_building_sets planet_modifier potential resources triggered_district_planet_modifier unlock` |
| `zones/shared_research_physics_zone` | `SPLIT` | `availability economy metadata tpm zone_config` | `base_buildtime icon included_building_sets planet_modifier potential resources triggered_district_planet_modifier unlock` |
| `zones/shared_research_society_zone` | `SPLIT` | `availability economy metadata tpm zone_config` | `base_buildtime icon included_building_sets planet_modifier potential resources triggered_district_planet_modifier unlock` |
| `zones/shared_research_zone` | `SPLIT` | `ai availability economy metadata tpm zone_config` | `ai_priority ai_resource_production ai_weight_coefficient base_buildtime icon included_building_sets planet_modifier potential resources triggered_district_planet_modifier unlock` |
| `zones/shared_research_zone_modifiers` | `WHOLE` | `tpm` | `triggered_district_planet_modifier` |
| `zones/shared_ring_world_zone_modifiers` | `WHOLE` | `tpm` | `triggered_district_planet_modifier` |
| `zones/shared_spawning_zone` | `SPLIT` | `ai availability economy metadata tpm zone_config` | `ai_priority base_buildtime icon included_building_sets max_buildings planet_modifier potential resources triggered_district_planet_modifier unlock` |
| `zones/shared_trade_zone` | `SPLIT` | `ai availability economy metadata tpm zone_config` | `ai_priority ai_weight_coefficient base_buildtime icon included_building_sets planet_modifier potential resources triggered_district_planet_modifier unlock` |
| `zones/shared_unity_bio_trophy_zone` | `SPLIT` | `ai availability economy metadata tpm zone_config` | `ai_priority ai_resource_production base_buildtime icon included_building_sets planet_modifier potential resources triggered_district_planet_modifier unlock` |
| `zones/shared_unity_spiritualist_zone` | `SPLIT` | `ai availability economy metadata tpm zone_config` | `ai_priority ai_resource_production base_buildtime icon included_building_sets planet_modifier potential resources triggered_district_planet_modifier unlock` |
| `zones/shared_unity_zone` | `SPLIT` | `ai availability economy metadata tpm zone_config` | `ai_priority ai_resource_production base_buildtime icon included_building_sets planet_modifier potential resources triggered_district_planet_modifier unlock` |
| `zones/shared_volatile_motes_zone` | `SPLIT` | `ai availability economy lifecycle metadata tpm zone_config` | `ai_priority base_buildtime convert_to icon included_building_sets planet_modifier potential resources triggered_desc triggered_district_planet_modifier unlock` |

### Split rules

- A `WHOLE` script is moved or expanded as a single semantic block inside the matching PIF category.
- A `SPLIT` script is expanded and distributed across categories.
- An empty script may be used as no-op source material, but does not create gameplay content.
- PIF-owned category scripts are the final compatibility layer.

## Normalizations

| Normalization | Reason | Validation requirement |
| --- | --- | --- |
| `planet_modifier` -> `triggered_planet_modifier` | Allows independent extension of modifier blocks. | Unconditional trigger must be equivalent to the static vanilla modifier. |
| `country_modifier` -> `triggered_country_modifier` | Allows independent extension of country-scope modifier blocks. | Expanded result must match vanilla semantics. |
| `district_planet_modifier` -> `triggered_district_planet_modifier` | Makes district-scoped zone modifiers extensible. | Condition must be unconditional or equivalent. |
| Vanilla `@variable` -> PIF variable | Creates object-specific tuning points instead of preserving shared vanilla variables. | Resolved PIF value must equal the original value. |
| Inline script expansion and split | Reduces conflict zones by moving content into PIF-owned category scripts. | Expanded PIF object must match expanded vanilla object after allowed normalizations. |
| Implicit zone building cap materialization | Zones with `zone_building_slots_add`, but without explicit `max_buildings`, receive explicit `max_buildings = 3`, matching `DEFAULT_MAX_PLANET_BUILDINGS_PER_ZONE`. | Allowed only for zones where vanilla already has `zone_building_slots_add`; max-only zones are not changed. |
| Shared building-capacity variable | `zone_building_slots_add` and `max_buildings` are controlled by one PIF variable. | Both generated values must reference the same raw variable in the generated PIF zone. |

## Parameter order

A category defines ownership of a parameter, but it does not override ordering. The generator and validator must preserve order-sensitive sections. Repeated blocks must not be sorted automatically when order may affect selection of the first valid target, tooltip display, or final effect application.

Important areas include `swap_type` / `swap_type_weight`, building filters, `convert_to`, and repeated modifier blocks.

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
- warning-level special cases without turning vanilla peculiarities into hard failures;
- invariant: if a zone has `zone_building_slots_add`, it must reference the same variable as `max_buildings`.

Current result: **120 / 120 OK**, failed: **0**.

## Runtime validation

Static validation confirms structural equivalence, but runtime smoke testing is still required because the engine may depend on context that is not visible in AST comparison.

A minimal runtime check should include starting a new game, opening the planetary UI, checking regular empire, hive, machine, and corporate contexts, habitats/ringworld/ecumenopolis when possible, and reviewing `error.log` for errors related to `pif_` files.

## Layer statistics

| Metric | Value |
| --- | --- |
| Objects | 120 |
| Source files | 5 |
| Parameter names after expansion | 22 |
| Category inline scripts | 720 |
| Variable files | 14 |
| PIF variables | 1544 |
| Reachable inline scripts | 39 |
| Inline scripts WHOLE | 19 |
| Inline scripts SPLIT | 20 |
| Validation checked | 120 |
| Validation OK | 120 |
| Validation failed | 0 |

## Parameter statistics

| Parameter | Objects | Category | Action |
| --- | --- | --- | --- |
| `ai_priority` | 91 | AI | Move into the corresponding PIF-owned category inline script. |
| `ai_resource_production` | 34 | AI | Move into the corresponding PIF-owned category inline script. |
| `ai_weight_coefficient` | 25 | AI | Move into the corresponding PIF-owned category inline script. |
| `planet_limit` | 13 | AVAILABILITY | Move into the corresponding PIF-owned category inline script. |
| `potential` | 119 | AVAILABILITY | Move into the corresponding PIF-owned category inline script. |
| `show_in_tech` | 10 | AVAILABILITY | Move into the corresponding PIF-owned category inline script. |
| `unlock` | 119 | AVAILABILITY | Move into the corresponding PIF-owned category inline script. |
| `resources` | 118 | ECONOMY | Move into the corresponding PIF-owned category inline script. |
| `convert_to` | 41 | LIFECYCLE | Move into the corresponding PIF-owned category inline script. |
| `base_buildtime` | 118 | METADATA | Keep in the root object. |
| `icon` | 119 | METADATA | Keep in the root object. |
| `max_buildings` | 120 | METADATA | Keep in the root object. For 103 zones, the value is materialized from implicit default `3` because they have `zone_building_slots_add`. |
| `max_buildings_planet_class` | 1 | METADATA | Keep in the root object. |
| `swap_type` | 77 | METADATA | Keep in the root object. |
| `swap_type_weight` | 77 | METADATA | Keep in the root object. |
| `triggered_desc` | 34 | METADATA | Keep in the root object. |
| `planet_modifier` | 112 | TPM | Normalize into triggered equivalent and then classify. |
| `triggered_district_planet_modifier` | 117 | TPM | Move into the corresponding PIF-owned category inline script. |
| `excluded_building_sets` | 15 | ZONE_CONFIG | Move into the corresponding PIF-owned category inline script. |
| `include` | 4 | ZONE_CONFIG | Move into the corresponding PIF-owned category inline script. |
| `included_building_sets` | 117 | ZONE_CONFIG | Move into the corresponding PIF-owned category inline script. |
| `zone_sets` | 120 | ZONE_CONFIG | Move into the corresponding PIF-owned category inline script. |

## Special cases and technical warnings

- `swap_type` remains metadata because it defines the visual district mask and must preserve order near `swap_type_weight`.
- `zone_sets` and building set filters are the compatibility bridge between zones and buildings and therefore belong to `ZONE_CONFIG`.
- Static modifiers are normalized into triggered equivalents when required for extensibility.
- `zone_building_slots_add` no longer gets separate `building_capacity_zone_building_slots_add` variables; it uses the matching `building_capacity_max_buildings` variable.
- The 8 zones that have only `max_buildings` and no `zone_building_slots_add` remain without tooltip/modifier additions and do not receive new TPM logic.

## Affected vanilla objects

This section lists the vanilla objects overridden by PIF for this layer.

### `zones/00_zones.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `zone_default` | `zone` | `common/zones/pif_00_zones_zone_default.txt` |
| `zone_urban` | `zone` | `common/zones/pif_00_zones_zone_urban.txt` |
| `zone_industrial` | `zone` | `common/zones/pif_00_zones_zone_industrial.txt` |
| `zone_foundry` | `zone` | `common/zones/pif_00_zones_zone_foundry.txt` |
| `zone_factory` | `zone` | `common/zones/pif_00_zones_zone_factory.txt` |
| `zone_research_unity` | `zone` | `common/zones/pif_00_zones_zone_research_unity.txt` |
| `zone_research` | `zone` | `common/zones/pif_00_zones_zone_research.txt` |
| `zone_research_physics` | `zone` | `common/zones/pif_00_zones_zone_research_physics.txt` |
| `zone_research_society` | `zone` | `common/zones/pif_00_zones_zone_research_society.txt` |
| `zone_research_engineering` | `zone` | `common/zones/pif_00_zones_zone_research_engineering.txt` |
| `zone_unity` | `zone` | `common/zones/pif_00_zones_zone_unity.txt` |
| `zone_unity_spiritualist` | `zone` | `common/zones/pif_00_zones_zone_unity_spiritualist.txt` |
| `zone_unity_bio_trophy` | `zone` | `common/zones/pif_00_zones_zone_unity_bio_trophy.txt` |
| `zone_fortress` | `zone` | `common/zones/pif_00_zones_zone_fortress.txt` |
| `zone_trade` | `zone` | `common/zones/pif_00_zones_zone_trade.txt` |
| `zone_resort` | `zone` | `common/zones/pif_00_zones_zone_resort.txt` |
| `zone_resort_entertainment` | `zone` | `common/zones/pif_00_zones_zone_resort_entertainment.txt` |
| `zone_resort_zoo` | `zone` | `common/zones/pif_00_zones_zone_resort_zoo.txt` |
| `zone_resort_grand_museum` | `zone` | `common/zones/pif_00_zones_zone_resort_grand_museum.txt` |
| `zone_resort_hunting_ground` | `zone` | `common/zones/pif_00_zones_zone_resort_hunting_ground.txt` |
| `zone_resort_spiritual_retreat` | `zone` | `common/zones/pif_00_zones_zone_resort_spiritual_retreat.txt` |
| `zone_resort_restoration_enclave` | `zone` | `common/zones/pif_00_zones_zone_resort_restoration_enclave.txt` |
| `zone_resort_proving_grounds` | `zone` | `common/zones/pif_00_zones_zone_resort_proving_grounds.txt` |
| `zone_minerals` | `zone` | `common/zones/pif_00_zones_zone_minerals.txt` |
| `zone_betharian` | `zone` | `common/zones/pif_00_zones_zone_betharian.txt` |
| `zone_rare_crystals` | `zone` | `common/zones/pif_00_zones_zone_rare_crystals.txt` |
| `zone_minerals_physics` | `zone` | `common/zones/pif_00_zones_zone_minerals_physics.txt` |
| `zone_energy` | `zone` | `common/zones/pif_00_zones_zone_energy.txt` |
| `zone_volatile_motes` | `zone` | `common/zones/pif_00_zones_zone_volatile_motes.txt` |
| `zone_food` | `zone` | `common/zones/pif_00_zones_zone_food.txt` |
| `zone_anglers` | `zone` | `common/zones/pif_00_zones_zone_anglers.txt` |
| `zone_exotic_gases` | `zone` | `common/zones/pif_00_zones_zone_exotic_gases.txt` |
| `zone_spawning` | `zone` | `common/zones/pif_00_zones_zone_spawning.txt` |
| `zone_machine_replication` | `zone` | `common/zones/pif_00_zones_zone_machine_replication.txt` |
| `zone_subterranean_urban` | `zone` | `common/zones/pif_00_zones_zone_subterranean_urban.txt` |
| `zone_agrarian_urban` | `zone` | `common/zones/pif_00_zones_zone_agrarian_urban.txt` |
| `zone_agrarian_anglers` | `zone` | `common/zones/pif_00_zones_zone_agrarian_anglers.txt` |
| `zone_cosmogenesis_default` | `zone` | `common/zones/pif_00_zones_zone_cosmogenesis_default.txt` |

### `zones/01_habitat_zones.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `zone_habitat_knights` | `zone` | `common/zones/pif_01_habitat_zones_zone_habitat_knights.txt` |
| `zone_habitat_hydroponics` | `zone` | `common/zones/pif_01_habitat_zones_zone_habitat_hydroponics.txt` |
| `zone_habitat_research` | `zone` | `common/zones/pif_01_habitat_zones_zone_habitat_research.txt` |
| `zone_habitat_research_unity` | `zone` | `common/zones/pif_01_habitat_zones_zone_habitat_research_unity.txt` |
| `zone_habitat_rare_crystals` | `zone` | `common/zones/pif_01_habitat_zones_zone_habitat_rare_crystals.txt` |
| `zone_habitat_volatile_motes` | `zone` | `common/zones/pif_01_habitat_zones_zone_habitat_volatile_motes.txt` |
| `zone_habitat_exotic_gases` | `zone` | `common/zones/pif_01_habitat_zones_zone_habitat_exotic_gases.txt` |

### `zones/02_special_zones.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `zone_payback_enlightenment` | `zone` | `common/zones/pif_02_special_zones_zone_payback_enlightenment.txt` |
| `zone_broken_shackles_memorial` | `zone` | `common/zones/pif_02_special_zones_zone_broken_shackles_memorial.txt` |
| `zone_central_spire` | `zone` | `common/zones/pif_02_special_zones_zone_central_spire.txt` |

### `zones/03_wilderness_zones.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `zone_urban_wilderness` | `zone` | `common/zones/pif_03_wilderness_zones_zone_urban_wilderness.txt` |
| `zone_foundry_wilderness` | `zone` | `common/zones/pif_03_wilderness_zones_zone_foundry_wilderness.txt` |
| `zone_research_wilderness` | `zone` | `common/zones/pif_03_wilderness_zones_zone_research_wilderness.txt` |
| `zone_unity_wilderness` | `zone` | `common/zones/pif_03_wilderness_zones_zone_unity_wilderness.txt` |
| `zone_research_unity_wilderness` | `zone` | `common/zones/pif_03_wilderness_zones_zone_research_unity_wilderness.txt` |
| `zone_trade_wilderness` | `zone` | `common/zones/pif_03_wilderness_zones_zone_trade_wilderness.txt` |
| `zone_fortress_wilderness` | `zone` | `common/zones/pif_03_wilderness_zones_zone_fortress_wilderness.txt` |
| `zone_minerals_wilderness` | `zone` | `common/zones/pif_03_wilderness_zones_zone_minerals_wilderness.txt` |
| `zone_energy_wilderness` | `zone` | `common/zones/pif_03_wilderness_zones_zone_energy_wilderness.txt` |
| `zone_food_wilderness` | `zone` | `common/zones/pif_03_wilderness_zones_zone_food_wilderness.txt` |

### `zones/04_secondary_zones.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `zone_industrial_arcology` | `zone` | `common/zones/pif_04_secondary_zones_zone_industrial_arcology.txt` |
| `zone_foundry_arcology` | `zone` | `common/zones/pif_04_secondary_zones_zone_foundry_arcology.txt` |
| `zone_factory_arcology` | `zone` | `common/zones/pif_04_secondary_zones_zone_factory_arcology.txt` |
| `zone_research_arcology` | `zone` | `common/zones/pif_04_secondary_zones_zone_research_arcology.txt` |
| `zone_research_physics_arcology` | `zone` | `common/zones/pif_04_secondary_zones_zone_research_physics_arcology.txt` |
| `zone_research_society_arcology` | `zone` | `common/zones/pif_04_secondary_zones_zone_research_society_arcology.txt` |
| `zone_research_engineering_arcology` | `zone` | `common/zones/pif_04_secondary_zones_zone_research_engineering_arcology.txt` |
| `zone_unity_arcology` | `zone` | `common/zones/pif_04_secondary_zones_zone_unity_arcology.txt` |
| `zone_unity_spiritualist_arcology` | `zone` | `common/zones/pif_04_secondary_zones_zone_unity_spiritualist_arcology.txt` |
| `zone_unity_bio_trophy_arcology` | `zone` | `common/zones/pif_04_secondary_zones_zone_unity_bio_trophy_arcology.txt` |
| `zone_fortress_arcology` | `zone` | `common/zones/pif_04_secondary_zones_zone_fortress_arcology.txt` |
| `zone_trade_arcology` | `zone` | `common/zones/pif_04_secondary_zones_zone_trade_arcology.txt` |
| `zone_industrial_ring_world` | `zone` | `common/zones/pif_04_secondary_zones_zone_industrial_ring_world.txt` |
| `zone_foundry_ring_world` | `zone` | `common/zones/pif_04_secondary_zones_zone_foundry_ring_world.txt` |
| `zone_factory_ring_world` | `zone` | `common/zones/pif_04_secondary_zones_zone_factory_ring_world.txt` |
| `zone_research_ring_world` | `zone` | `common/zones/pif_04_secondary_zones_zone_research_ring_world.txt` |
| `zone_research_physics_ring_world` | `zone` | `common/zones/pif_04_secondary_zones_zone_research_physics_ring_world.txt` |
| `zone_research_society_ring_world` | `zone` | `common/zones/pif_04_secondary_zones_zone_research_society_ring_world.txt` |
| `zone_research_engineering_ring_world` | `zone` | `common/zones/pif_04_secondary_zones_zone_research_engineering_ring_world.txt` |
| `zone_unity_ring_world` | `zone` | `common/zones/pif_04_secondary_zones_zone_unity_ring_world.txt` |
| `zone_unity_spiritualist_ring_world` | `zone` | `common/zones/pif_04_secondary_zones_zone_unity_spiritualist_ring_world.txt` |
| `zone_unity_bio_trophy_ring_world` | `zone` | `common/zones/pif_04_secondary_zones_zone_unity_bio_trophy_ring_world.txt` |
| `zone_fortress_ring_world` | `zone` | `common/zones/pif_04_secondary_zones_zone_fortress_ring_world.txt` |
| `zone_trade_ring_world` | `zone` | `common/zones/pif_04_secondary_zones_zone_trade_ring_world.txt` |
| `zone_food_ring_world` | `zone` | `common/zones/pif_04_secondary_zones_zone_food_ring_world.txt` |
| `zone_energy_ring_world` | `zone` | `common/zones/pif_04_secondary_zones_zone_energy_ring_world.txt` |
| `zone_industrial_nexus` | `zone` | `common/zones/pif_04_secondary_zones_zone_industrial_nexus.txt` |
| `zone_foundry_nexus` | `zone` | `common/zones/pif_04_secondary_zones_zone_foundry_nexus.txt` |
| `zone_factory_nexus` | `zone` | `common/zones/pif_04_secondary_zones_zone_factory_nexus.txt` |
| `zone_research_nexus` | `zone` | `common/zones/pif_04_secondary_zones_zone_research_nexus.txt` |
| `zone_research_physics_nexus` | `zone` | `common/zones/pif_04_secondary_zones_zone_research_physics_nexus.txt` |
| `zone_research_society_nexus` | `zone` | `common/zones/pif_04_secondary_zones_zone_research_society_nexus.txt` |
| `zone_research_engineering_nexus` | `zone` | `common/zones/pif_04_secondary_zones_zone_research_engineering_nexus.txt` |
| `zone_unity_nexus` | `zone` | `common/zones/pif_04_secondary_zones_zone_unity_nexus.txt` |
| `zone_unity_spiritualist_nexus` | `zone` | `common/zones/pif_04_secondary_zones_zone_unity_spiritualist_nexus.txt` |
| `zone_unity_bio_trophy_nexus` | `zone` | `common/zones/pif_04_secondary_zones_zone_unity_bio_trophy_nexus.txt` |
| `zone_fortress_nexus` | `zone` | `common/zones/pif_04_secondary_zones_zone_fortress_nexus.txt` |
| `zone_trade_nexus` | `zone` | `common/zones/pif_04_secondary_zones_zone_trade_nexus.txt` |
| `zone_minerals_nexus` | `zone` | `common/zones/pif_04_secondary_zones_zone_minerals_nexus.txt` |
| `zone_betharian_nexus` | `zone` | `common/zones/pif_04_secondary_zones_zone_betharian_nexus.txt` |
| `zone_rare_crystals_nexus` | `zone` | `common/zones/pif_04_secondary_zones_zone_rare_crystals_nexus.txt` |
| `zone_energy_nexus` | `zone` | `common/zones/pif_04_secondary_zones_zone_energy_nexus.txt` |
| `zone_volatile_motes_nexus` | `zone` | `common/zones/pif_04_secondary_zones_zone_volatile_motes_nexus.txt` |
| `zone_exotic_gases_nexus` | `zone` | `common/zones/pif_04_secondary_zones_zone_exotic_gases_nexus.txt` |
| `zone_industrial_hive` | `zone` | `common/zones/pif_04_secondary_zones_zone_industrial_hive.txt` |
| `zone_foundry_hive` | `zone` | `common/zones/pif_04_secondary_zones_zone_foundry_hive.txt` |
| `zone_factory_hive` | `zone` | `common/zones/pif_04_secondary_zones_zone_factory_hive.txt` |
| `zone_research_hive` | `zone` | `common/zones/pif_04_secondary_zones_zone_research_hive.txt` |
| `zone_research_physics_hive` | `zone` | `common/zones/pif_04_secondary_zones_zone_research_physics_hive.txt` |
| `zone_research_society_hive` | `zone` | `common/zones/pif_04_secondary_zones_zone_research_society_hive.txt` |
| `zone_research_engineering_hive` | `zone` | `common/zones/pif_04_secondary_zones_zone_research_engineering_hive.txt` |
| `zone_unity_hive` | `zone` | `common/zones/pif_04_secondary_zones_zone_unity_hive.txt` |
| `zone_fortress_hive` | `zone` | `common/zones/pif_04_secondary_zones_zone_fortress_hive.txt` |
| `zone_trade_hive` | `zone` | `common/zones/pif_04_secondary_zones_zone_trade_hive.txt` |
| `zone_food_hive` | `zone` | `common/zones/pif_04_secondary_zones_zone_food_hive.txt` |
| `zone_exotic_gases_hive` | `zone` | `common/zones/pif_04_secondary_zones_zone_exotic_gases_hive.txt` |
| `zone_minerals_hive` | `zone` | `common/zones/pif_04_secondary_zones_zone_minerals_hive.txt` |
| `zone_betharian_hive` | `zone` | `common/zones/pif_04_secondary_zones_zone_betharian_hive.txt` |
| `zone_rare_crystals_hive` | `zone` | `common/zones/pif_04_secondary_zones_zone_rare_crystals_hive.txt` |
| `zone_energy_hive` | `zone` | `common/zones/pif_04_secondary_zones_zone_energy_hive.txt` |
| `zone_volatile_motes_hive` | `zone` | `common/zones/pif_04_secondary_zones_zone_volatile_motes_hive.txt` |
| `zone_spawning_hive` | `zone` | `common/zones/pif_04_secondary_zones_zone_spawning_hive.txt` |

## Source files and documentation used

| Type | Files |
| --- | --- |
| Vanilla object files | `common/zones/*.txt` |
| Inline scripts | reachable files under `common/inline_scripts/` |
| Scripted variables | `common/scripted_variables/*.txt` |
| Object documentation | zone documentation files and actual `common/zones` objects |
| Generated reports | `Analytics/reports/zones/` |
