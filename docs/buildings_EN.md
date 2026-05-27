# Buildings — PIF Technical Specification

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

This document describes the technical organization of the `buildings` layer in Planetary Infrastructure Framework. It defines how PIF analyzes buildings and building-like objects, including capitals, branch office buildings, holdings, and special non-`building_` keys, assigns parameters to categories, classifies modifier blocks by content, extracts domain variables, and validates preservation of vanilla behavior.

## Layer overview

`buildings` are the largest planetary infrastructure layer. They include not only regular `building_*` objects, but also capitals, branch office buildings, overlord holdings, and special building-like keys without the `building_` prefix.

Buildings connect almost every gameplay area of planetary infrastructure: construction, cost and upkeep, jobs, planet state, country effects, lifecycle, upgrades, conversion, AI, and branch or holding mechanics. PIF therefore uses a more detailed category structure than districts and zones and classifies modifier-carrier blocks by their actual content.

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
| regular | 366 | Regular building objects that are not capitals, branch office buildings, or holdings. |
| capital | 41 | Buildings with `capital = yes` and `capital_tier`. |
| branch | 35 | Branch office buildings with `owner_type = corporate`. |
| holding | 30 | Overlord holdings with `owner_type = subject_holding` or a `holding_*` key. |
| special | 18 | Building-like objects without the `building_` prefix. |

## PIF layer architecture

### Object files

Each vanilla object is moved into a separate normalized PIF object file:

```txt
common/buildings/pif_<vanilla_file_stem>_<building_key>.txt
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
common/inline_scripts/pif/buildings/<building_key>/<category>.txt
```

A category script is the minimal conflict zone. A mod that changes only the economy of an object should not need to overwrite availability, lifecycle, or AI of the same object.

### Category order

Category script order is fixed and is part of the PIF schema:

```txt
building_config
availability
economy
lifecycle
jobs
country_jobs
economic_modifiers
pop_modifiers
planet_state
tpm
ai
```

The order is required for reproducible generation, readability, and correct static validation. It must not be changed by incidental sorting.

## Parameter categories

Parameter categories define which PIF-owned inline script owns a particular part of the object. A parameter category does not have to match the variable domain. Modifier-carrier parameters are classified by block content; `triggered_planet_modifier` itself is not treated as a category.

| Category | Location | Purpose | Parameters |
| --- | --- | --- | --- |
| METADATA | Root object | Identity, UI, and engine-sensitive fields. | `category`, `owner_type`, `capital`, `capital_tier`, icons, descriptions, `base_buildtime`. |
| BUILDING_CONFIG | Inline script | Building set compatibility. | `building_sets`. |
| AVAILABILITY | Inline script | Construction conditions, visibility, and limits. | `potential`, `allow`, `can_build`, `prerequisites`, `planet_limit`, `empire_limit`. |
| ECONOMY | Inline script | Cost, upkeep, and building resource block. | `resources`. |
| LIFECYCLE | Inline script | State, upgrades, conversions, and construction events. | `can_demolish`, `can_be_ruined`, `destroy_trigger`, `convert_to`, `upgrades`, `on_*`. |
| JOBS | Inline script | Job additions and job-related planet-scope modifiers. | `job_*_add` and related clean modifier blocks. |
| COUNTRY_JOBS | Inline script | Country-scope job-like effects. | `job_capital_trader_add` and similar cases. |
| ECONOMIC_MODIFIERS | Inline script | Production/output/upkeep modifier blocks. | `planet_jobs_*_produces_*`, `planet_*_upkeep_*`. |
| POP_MODIFIERS | Inline script | Pop growth, happiness, habitability, and workforce effects. | Pop-related modifier keys. |
| PLANET_STATE | Inline script | Housing, amenities, crime, stability, slots, and defensive state. | `planet_housing_add`, `planet_amenities_add`, `planetary_ftl_inhibitor`. |
| TPM | Inline script | Fallback for mixed, rare, system, or special modifier blocks. | Mixed modifier carriers and rare special effects. |
| AI | Inline script | AI weighting and resource hints. | `ai_resource_production`, `ai_weight`, `ai_weight_coefficient`, etc. |

## Variable categories

| Domain file | Variables | Purpose |
| --- | --- | --- |
| `pif_buildings_ai_variables.txt` | 244 | Building AI weights and hints. |
| `pif_buildings_availability_thresholds_variables.txt` | 37 | Meaningful availability thresholds. |
| `pif_buildings_construction_variables.txt` | 658 | Build time and construction speed values. |
| `pif_buildings_cost_variables.txt` | 783 | Construction costs from building resources. |
| `pif_buildings_country_jobs_variables.txt` | 27 | Country-scope job-like values from buildings. |
| `pif_buildings_economic_modifiers_variables.txt` | 918 | Production/output/upkeep modifier values from buildings. |
| `pif_buildings_jobs_variables.txt` | 1308 | Job additions and job-related values from buildings. |
| `pif_buildings_limits_variables.txt` | 299 | Planet, empire, and cap limits. |
| `pif_buildings_planet_state_variables.txt` | 354 | Housing, amenities, crime, stability, slots, and defensive state. |
| `pif_buildings_pop_modifiers_variables.txt` | 468 | Pop growth, happiness, habitability, and workforce modifiers. |
| `pif_buildings_tpm_variables.txt` | 89 | Meaningful fallback values from mixed or rare modifier blocks. |
| `pif_buildings_upkeep_variables.txt` | 696 | Building upkeep values. |

Total: **12** variable files and **5881** variables.

## Inline Scripts

### Inline script policy

Vanilla inline scripts are used as source material for PIF-owned category scripts. `WHOLE` means that the expanded script belongs to one category. `SPLIT` means that the expanded script must be distributed across categories. This layer has **54** reachable inline scripts: **42** `WHOLE`, **12** `SPLIT`.

### Reachable inline scripts

| Inline script | Decision | Categories | Parameters |
| --- | --- | --- | --- |
| `buildings/clone_army_vat_output` | `WHOLE` | `pop_modifiers` | `triggered_planet_modifier triggered_planet_pop_group_modifier_for_species` |
| `buildings/on_all_capital_buildings` | `SPLIT` | `economic_modifiers jobs planet_state pop_modifiers tpm` | `triggered_country_modifier triggered_planet_modifier` |
| `buildings/on_all_habitat_capital_buildings` | `WHOLE` | `planet_state` | `triggered_planet_modifier` |
| `buildings/on_all_wilderness_buildings_districts` | `SPLIT` | `lifecycle planet_state` | `on_queued on_unqueued triggered_planet_modifier` |
| `buildings/planet_job_resource_produces_add` | `WHOLE` | `economic_modifiers` | `triggered_planet_modifier` |
| `buildings/regular_empire_capital_jobs` | `WHOLE` | `jobs` | `triggered_planet_modifier` |
| `buildings/wilderness_buildings_potential_destroy` | `SPLIT` | `availability lifecycle` | `destroy_trigger potential` |
| `cosmic_storms/PlanetaryShieldOnBuiltDestroy` | `WHOLE` | `lifecycle` | `on_built on_destroy` |
| `cosmic_storms/StormBuildingModifiers` | `WHOLE` | `economic_modifiers` | `triggered_planet_modifier` |
| `districts/ai_alloys_extra_weighting` | `WHOLE` | `ai` | `ai_resource_production` |
| `districts/ai_consumer_goods_extra_weighting` | `WHOLE` | `ai` | `ai_resource_production` |
| `districts/ai_research_engineering_extra_weighting` | `WHOLE` | `ai` | `ai_resource_production` |
| `districts/ai_research_extra_weighting` | `WHOLE` | `ai` | `ai_resource_production` |
| `districts/ai_research_physics_extra_weighting` | `WHOLE` | `ai` | `ai_resource_production` |
| `districts/ai_research_society_extra_weighting` | `WHOLE` | `ai` | `ai_resource_production` |
| `jobs/bath_attendant_add` | `WHOLE` | `jobs` | `triggered_planet_modifier` |
| `jobs/biologists_add` | `WHOLE` | `jobs` | `triggered_planet_modifier` |
| `jobs/clerks_add` | `WHOLE` | `jobs` | `triggered_planet_modifier` |
| `jobs/enforcers_add` | `WHOLE` | `jobs` | `triggered_planet_modifier` |
| `jobs/engineers_add` | `WHOLE` | `jobs` | `triggered_planet_modifier` |
| `jobs/entertainers_add` | `WHOLE` | `jobs` | `triggered_planet_modifier` |
| `jobs/factory_add` | `WHOLE` | `jobs` | `triggered_planet_modifier` |
| `jobs/farmers_add` | `WHOLE` | `jobs` | `triggered_planet_modifier` |
| `jobs/foundry_add` | `WHOLE` | `jobs` | `triggered_planet_modifier` |
| `jobs/healthcare_add` | `WHOLE` | `jobs` | `triggered_planet_modifier` |
| `jobs/miners_add` | `WHOLE` | `jobs` | `triggered_planet_modifier` |
| `jobs/mortal_initiates_add` | `WHOLE` | `jobs` | `triggered_planet_modifier` |
| `jobs/physicists_add` | `WHOLE` | `jobs` | `triggered_planet_modifier` |
| `jobs/politician_add` | `WHOLE` | `jobs` | `triggered_planet_modifier` |
| `jobs/politician_add_from_civic` | `WHOLE` | `jobs` | `triggered_planet_modifier` |
| `jobs/priests_add` | `WHOLE` | `jobs` | `triggered_planet_modifier` |
| `jobs/researchers_add` | `WHOLE` | `jobs` | `triggered_planet_modifier` |
| `jobs/roboticist_add` | `WHOLE` | `jobs` | `triggered_planet_modifier` |
| `jobs/soldiers_add` | `WHOLE` | `jobs` | `triggered_planet_modifier` |
| `jobs/spawning_drone_add` | `WHOLE` | `jobs` | `triggered_planet_modifier` |
| `jobs/technicians_add` | `WHOLE` | `jobs` | `triggered_planet_modifier` |
| `jobs/telepaths_add` | `WHOLE` | `jobs` | `triggered_planet_modifier` |
| `jobs/trader_add` | `WHOLE` | `jobs` | `triggered_planet_modifier` |
| `jobs/unity_jobs_add` | `WHOLE` | `jobs` | `triggered_planet_modifier` |
| `jobs/wranglers_add` | `WHOLE` | `jobs` | `triggered_planet_modifier` |
| `shroud/buildings/experimentation_chambers_jobs` | `WHOLE` | `jobs` | `triggered_planet_modifier` |
| `shroud/buildings/lifecrypt_1_conditions` | `SPLIT` | `availability lifecycle` | `convert_to prerequisites` |
| `shroud/buildings/lifecrypt_1_modifiers` | `SPLIT` | `metadata tpm` | `planet_modifier triggered_desc` |
| `shroud/buildings/lifecrypt_1_modifiers_gestalt` | `SPLIT` | `economic_modifiers jobs metadata` | `planet_modifier triggered_desc triggered_planet_modifier` |
| `shroud/buildings/lifecrypt_1_resources` | `WHOLE` | `economy` | `resources` |
| `shroud/buildings/lifecrypt_2_conditions` | `SPLIT` | `availability lifecycle` | `allow convert_to prerequisites` |
| `shroud/buildings/lifecrypt_2_modifiers` | `SPLIT` | `metadata tpm` | `planet_modifier triggered_desc` |
| `shroud/buildings/lifecrypt_2_modifiers_gestalt` | `SPLIT` | `economic_modifiers jobs metadata` | `planet_modifier triggered_desc triggered_planet_modifier` |
| `shroud/buildings/lifecrypt_2_resources` | `WHOLE` | `economy` | `resources` |
| `shroud/buildings/lifecrypt_3_conditions` | `SPLIT` | `availability lifecycle` | `allow convert_to prerequisites` |
| `shroud/buildings/lifecrypt_3_modifiers` | `SPLIT` | `metadata tpm` | `planet_modifier triggered_desc` |
| `shroud/buildings/lifecrypt_3_modifiers_gestalt` | `SPLIT` | `economic_modifiers jobs metadata` | `planet_modifier triggered_desc triggered_planet_modifier` |
| `shroud/buildings/lifecrypt_3_resources` | `WHOLE` | `economy` | `resources` |
| `shroud/jobs/colonist_add` | `WHOLE` | `jobs` | `triggered_planet_modifier` |

### Split rules

- A `WHOLE` script is moved or expanded as a single semantic block inside the matching PIF category.
- A `SPLIT` script is expanded and distributed across categories.
- An empty script may be used as no-op source material, but does not create gameplay content.
- PIF-owned category scripts are the final compatibility layer.
- If one modifier block mixes several semantic groups, it is not split line-by-line and is moved to the `TPM` fallback.

## Normalizations

| Normalization | Reason | Validation requirement |
| --- | --- | --- |
| `planet_modifier` -> `triggered_planet_modifier` | Allows independent extension of modifier blocks. | Unconditional trigger must be equivalent to the static vanilla modifier. |
| `country_modifier` -> `triggered_country_modifier` | Allows independent extension of country-scope modifier blocks. | Expanded result must match vanilla semantics. |
| Vanilla `@variable` -> PIF variable | Creates object-specific tuning points instead of preserving shared vanilla variables. | Resolved PIF value must equal the original value. |
| Inline script expansion and split | Reduces conflict zones by moving content into PIF-owned category scripts. | Expanded PIF object must match expanded vanilla object after allowed normalizations. |

## Parameter order

A category defines ownership of a parameter, but it does not override ordering. The generator and validator must preserve order-sensitive sections. Repeated blocks must not be sorted automatically when order may affect selection of the first valid target, tooltip display, or final effect application.

Important areas include `upgrades`, `convert_to`, repeated modifier blocks, lifecycle effects, and category inline call order.

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

Current result: **490 / 490 OK**, failed: **0**.

## Runtime validation

Static validation confirms structural equivalence, but runtime smoke testing is still required because the engine may depend on context that is not visible in AST comparison.

A minimal runtime check should include starting a new game, opening the planetary UI, checking regular empire, hive, machine, and corporate contexts, habitats/ringworld/ecumenopolis when possible, and reviewing `error.log` for errors related to `pif_` files.

## Layer statistics

| Metric | Value |
| --- | --- |
| Objects | 490 |
| Source files | 26 |
| Parameter names after expansion | 53 |
| Category inline scripts | 5390 |
| Variable files | 12 |
| PIF variables | 5881 |
| Reachable inline scripts | 54 |
| Inline scripts WHOLE | 42 |
| Inline scripts SPLIT | 12 |
| Validation checked | 490 |
| Validation OK | 490 |
| Validation failed | 0 |

## Parameter statistics

| Parameter | Type | Total | Regular | Capital | Branch | Holding | Special | Purpose | Category | Action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `additional_ai_weight` | number / scalar | 23 | 9 | 14 | 0 | 0 | 0 | Additional AI weight for evaluating the object. | AI | Move into the corresponding PIF-owned category inline script. |
| `ai_estimate_without_unemployment` | block / value | 55 | 49 | 6 | 0 | 0 | 0 | Instructs AI to estimate the object without unemployment. | AI | Move into the corresponding PIF-owned category inline script. |
| `ai_resource_production` | block / value | 55 | 54 | 0 | 1 | 0 | 0 | AI hint describing the resource role of the object. | AI | Move into the corresponding PIF-owned category inline script. |
| `ai_weight` | block / value | 33 | 0 | 0 | 33 | 0 | 0 | AI weight block for selecting the object. | AI | Move into the corresponding PIF-owned category inline script. |
| `ai_weight_coefficient` | number / scalar | 39 | 38 | 1 | 0 | 0 | 0 | AI weight coefficient. | AI | Move into the corresponding PIF-owned category inline script. |
| `custom_storm_ai_weight` | block / value | 11 | 11 | 0 | 0 | 0 | 0 | Special AI weight in cosmic storm context. | AI | Move into the corresponding PIF-owned category inline script. |
| `exempt_from_ai_planet_specialization` | block / value | 24 | 24 | 0 | 0 | 0 | 0 | Exemption from AI planet specialization. | AI | Move into the corresponding PIF-owned category inline script. |
| `allow` | trigger block | 262 | 208 | 18 | 8 | 18 | 10 | Condition for whether the action is currently allowed. | AVAILABILITY | Move into the corresponding PIF-owned category inline script. |
| `base_cap_amount` | number / scalar | 14 | 12 | 0 | 2 | 0 | 0 | Base cap amount for capped buildings. | AVAILABILITY | Move into the corresponding PIF-owned category inline script. |
| `can_build` | yes/no | 260 | 209 | 41 | 0 | 0 | 10 | Allows or forbids normal construction. | AVAILABILITY | Move into the corresponding PIF-owned category inline script. |
| `district_limit` | number / scalar | 1 | 1 | 0 | 0 | 0 | 0 | Limit tied to districts. | AVAILABILITY | Move into the corresponding PIF-owned category inline script. |
| `empire_limit` | number / scalar | 34 | 28 | 1 | 0 | 2 | 3 | Limit of objects in an empire. | AVAILABILITY | Move into the corresponding PIF-owned category inline script. |
| `planet_limit` | number / scalar | 243 | 177 | 0 | 33 | 28 | 5 | Limit of objects on a planet. | AVAILABILITY | Move into the corresponding PIF-owned category inline script. |
| `potential` | trigger block | 463 | 350 | 41 | 35 | 29 | 8 | Base condition for object existence or visibility. | AVAILABILITY | Move into the corresponding PIF-owned category inline script. |
| `prerequisites` | list / block | 245 | 212 | 18 | 5 | 0 | 10 | List of technology or unlock requirements. | AVAILABILITY | Move into the corresponding PIF-owned category inline script. |
| `show_in_tech` | atom / enum | 38 | 38 | 0 | 0 | 0 | 0 | Explicit technology where the object is shown. | AVAILABILITY | Move into the corresponding PIF-owned category inline script. |
| `show_tech_unlock_if` | trigger block | 164 | 141 | 11 | 2 | 0 | 10 | Condition for showing the object as a technology unlock. | AVAILABILITY | Move into the corresponding PIF-owned category inline script. |
| `building_sets` | list / block | 425 | 366 | 41 | 0 | 0 | 18 | Specialized building parameter. | BUILDING_CONFIG | Move into the corresponding PIF-owned category inline script. |
| `resources` | resources block | 462 | 346 | 33 | 35 | 30 | 18 | Economic block: cost, upkeep, produces, and economic category. | ECONOMY | Move into the corresponding PIF-owned category inline script. |
| `can_be_disabled` | yes/no | 44 | 14 | 30 | 0 | 0 | 0 | Allows disabled state for a building. | LIFECYCLE | Move into the corresponding PIF-owned category inline script. |
| `can_be_ruined` | yes/no | 78 | 42 | 36 | 0 | 0 | 0 | Allows ruined state for a building. | LIFECYCLE | Move into the corresponding PIF-owned category inline script. |
| `can_demolish` | yes/no | 158 | 117 | 41 | 0 | 0 | 0 | Allows or forbids demolition. | LIFECYCLE | Move into the corresponding PIF-owned category inline script. |
| `convert_to` | list / block | 169 | 98 | 36 | 20 | 0 | 15 | List of conversion targets. | LIFECYCLE | Move into the corresponding PIF-owned category inline script. |
| `destroy_trigger` | trigger block | 371 | 316 | 10 | 21 | 9 | 15 | Condition for destruction or automatic conversion. | LIFECYCLE | Move into the corresponding PIF-owned category inline script. |
| `on_built` | effect block | 35 | 16 | 2 | 4 | 13 | 0 | Effect executed when construction completes. | LIFECYCLE | Move into the corresponding PIF-owned category inline script. |
| `on_destroy` | effect block | 33 | 19 | 0 | 3 | 11 | 0 | Effect executed when the object is destroyed. | LIFECYCLE | Move into the corresponding PIF-owned category inline script. |
| `on_enabled` | effect block | 5 | 5 | 0 | 0 | 0 | 0 | Effect executed when the object is enabled. | LIFECYCLE | Move into the corresponding PIF-owned category inline script. |
| `on_queued` | effect block | 101 | 93 | 5 | 0 | 0 | 3 | Effect executed when construction is queued. | LIFECYCLE | Move into the corresponding PIF-owned category inline script. |
| `on_repaired` | effect block | 9 | 9 | 0 | 0 | 0 | 0 | Effect executed when the object is repaired. | LIFECYCLE | Move into the corresponding PIF-owned category inline script. |
| `on_unqueued` | effect block | 101 | 93 | 5 | 0 | 0 | 3 | Effect executed when construction is removed from queue. | LIFECYCLE | Move into the corresponding PIF-owned category inline script. |
| `upgrades` | list / block | 188 | 147 | 31 | 0 | 0 | 10 | Building upgrade chain. | LIFECYCLE | Move into the corresponding PIF-owned category inline script. |
| `auto_generate_description` | yes/no | 2 | 2 | 0 | 0 | 0 | 0 | Controls automatic effect description generation. | METADATA | Keep in the root object. |
| `base_buildtime` | number / scalar | 454 | 346 | 25 | 35 | 30 | 18 | Base construction time. | METADATA | Keep in the root object. |
| `capital` | yes/no | 41 | 0 | 41 | 0 | 0 | 0 | Capital building flag. | METADATA | Keep in the root object. |
| `capital_tier` | number / scalar | 41 | 0 | 41 | 0 | 0 | 0 | Technical tier of a capital building. | METADATA | Keep in the root object. |
| `category` | atom / enum | 490 | 366 | 41 | 35 | 30 | 18 | Vanilla object category. | METADATA | Keep in the root object. |
| `custom_tooltip` | block / value | 37 | 10 | 0 | 27 | 0 | 0 | Additional tooltip. | METADATA | Keep in the root object. |
| `desc` | block / value | 9 | 9 | 0 | 0 | 0 | 0 | Direct or conditional description. | METADATA | Keep in the root object. |
| `icon` | atom / enum | 163 | 107 | 19 | 4 | 30 | 3 | Object icon. | METADATA | Keep in the root object. |
| `is_essential` | yes/no | 7 | 7 | 0 | 0 | 0 | 0 | Essential building flag. | METADATA | Keep in the root object. |
| `owner_type` | atom / enum | 65 | 0 | 0 | 35 | 30 | 0 | Owner type used by branch office or holding logic. | METADATA | Keep in the root object. |
| `position_priority` | number / scalar | 66 | 25 | 41 | 0 | 0 | 0 | Display ordering priority for buildings. | METADATA | Keep in the root object. |
| `ruined_icon` | atom / enum | 44 | 39 | 5 | 0 | 0 | 0 | Icon used for ruined state. | METADATA | Keep in the root object. |
| `skip_automation_upgrading` | yes/no | 1 | 1 | 0 | 0 | 0 | 0 | Disables automatic upgrade logic. | METADATA | Keep in the root object. |
| `triggered_desc` | block / value | 112 | 88 | 6 | 3 | 12 | 3 | Conditional descriptions and tooltips. | METADATA | Keep in the root object. |
| `planetary_ftl_inhibitor` | modifier / flag | 5 | 5 | 0 | 0 | 0 | 0 | Planetary FTL inhibitor flag. | PLANET_STATE | Move into the corresponding PIF-owned category inline script. |
| `country_modifier` | modifier / flag | 35 | 25 | 0 | 5 | 2 | 3 | Static country modifier carrier. | content-based modifier category | Classify the block by content; normalize static modifier carriers when required. |
| `planet_modifier` | modifier / flag | 296 | 236 | 39 | 3 | 18 | 0 | Static planet modifier carrier. | content-based modifier category | Classify the block by content; normalize static modifier carriers when required. |
| `system_modifier` | modifier / flag | 1 | 1 | 0 | 0 | 0 | 0 | System-level modifier carrier. | content-based modifier category | Classify the block by content; normalize static modifier carriers when required. |
| `triggered_country_modifier` | modifier / flag | 72 | 15 | 25 | 27 | 2 | 3 | Triggered country modifier carrier. | content-based modifier category | Classify the block by content; normalize static modifier carriers when required. |
| `triggered_planet_modifier` | modifier / flag | 373 | 261 | 34 | 34 | 26 | 18 | Triggered planet modifier carrier. | content-based modifier category | Classify the block by content; normalize static modifier carriers when required. |
| `triggered_planet_pop_group_modifier_for_all` | modifier / flag | 2 | 2 | 0 | 0 | 0 | 0 | Triggered modifier for all planet pop groups. | content-based modifier category | Classify the block by content; normalize static modifier carriers when required. |
| `triggered_planet_pop_group_modifier_for_species` | modifier / flag | 1 | 1 | 0 | 0 | 0 | 0 | Triggered modifier for species-specific pop groups. | content-based modifier category | Classify the block by content; normalize static modifier carriers when required. |

## Special cases and technical warnings

- All top-level objects from `common/buildings` must be loaded, not only `building_*`.
- `holding_*` and branch office buildings have their own structure and are not required to have `building_sets`.
- `building_citadel_uplink` preserves the vanilla duplicate `category`.
- `job_capital_trader_add` is treated as a warning-level reference, not a failure.

## Affected vanilla objects

This section lists the vanilla objects overridden by PIF for this layer.

### `buildings/00_capital_buildings.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `building_colony_shelter` | `capital` | `common/buildings/pif_00_capital_buildings_building_colony_shelter.txt` |
| `building_capital` | `capital` | `common/buildings/pif_00_capital_buildings_building_capital.txt` |
| `building_major_capital` | `capital` | `common/buildings/pif_00_capital_buildings_building_major_capital.txt` |
| `building_system_capital` | `capital` | `common/buildings/pif_00_capital_buildings_building_system_capital.txt` |
| `building_deployment_post` | `capital` | `common/buildings/pif_00_capital_buildings_building_deployment_post.txt` |
| `building_machine_capital` | `capital` | `common/buildings/pif_00_capital_buildings_building_machine_capital.txt` |
| `building_machine_major_capital` | `capital` | `common/buildings/pif_00_capital_buildings_building_machine_major_capital.txt` |
| `building_machine_system_capital` | `capital` | `common/buildings/pif_00_capital_buildings_building_machine_system_capital.txt` |
| `building_hive_capital` | `capital` | `common/buildings/pif_00_capital_buildings_building_hive_capital.txt` |
| `building_hive_major_capital` | `capital` | `common/buildings/pif_00_capital_buildings_building_hive_major_capital.txt` |
| `building_hab_capital` | `capital` | `common/buildings/pif_00_capital_buildings_building_hab_capital.txt` |
| `building_hab_major_capital` | `capital` | `common/buildings/pif_00_capital_buildings_building_hab_major_capital.txt` |
| `building_hab_system_capital` | `capital` | `common/buildings/pif_00_capital_buildings_building_hab_system_capital.txt` |
| `building_resort_capital` | `capital` | `common/buildings/pif_00_capital_buildings_building_resort_capital.txt` |
| `building_resort_major_capital` | `capital` | `common/buildings/pif_00_capital_buildings_building_resort_major_capital.txt` |
| `building_slave_capital` | `capital` | `common/buildings/pif_00_capital_buildings_building_slave_capital.txt` |
| `building_slave_major_capital` | `capital` | `common/buildings/pif_00_capital_buildings_building_slave_major_capital.txt` |
| `building_imperial_capital` | `capital` | `common/buildings/pif_00_capital_buildings_building_imperial_capital.txt` |
| `building_imperial_machine_capital` | `capital` | `common/buildings/pif_00_capital_buildings_building_imperial_machine_capital.txt` |
| `building_imperial_hive_capital` | `capital` | `common/buildings/pif_00_capital_buildings_building_imperial_hive_capital.txt` |

### `buildings/01_pop_assembly_buildings.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `building_robot_assembly_plant` | `regular` | `common/buildings/pif_01_pop_assembly_buildings_building_robot_assembly_plant.txt` |
| `building_robot_assembly_complex` | `regular` | `common/buildings/pif_01_pop_assembly_buildings_building_robot_assembly_complex.txt` |
| `building_machine_assembly_plant` | `regular` | `common/buildings/pif_01_pop_assembly_buildings_building_machine_assembly_plant.txt` |
| `building_machine_assembly_complex` | `regular` | `common/buildings/pif_01_pop_assembly_buildings_building_machine_assembly_complex.txt` |
| `building_spawning_pool` | `regular` | `common/buildings/pif_01_pop_assembly_buildings_building_spawning_pool.txt` |
| `building_offspring_nest` | `regular` | `common/buildings/pif_01_pop_assembly_buildings_building_offspring_nest.txt` |
| `building_necrophage_elevation_chamber` | `regular` | `common/buildings/pif_01_pop_assembly_buildings_building_necrophage_elevation_chamber.txt` |
| `building_necrophage_house_of_apotheosis` | `regular` | `common/buildings/pif_01_pop_assembly_buildings_building_necrophage_house_of_apotheosis.txt` |
| `building_clone_vats` | `regular` | `common/buildings/pif_01_pop_assembly_buildings_building_clone_vats.txt` |
| `building_clone_army_clone_vat` | `regular` | `common/buildings/pif_01_pop_assembly_buildings_building_clone_army_clone_vat.txt` |
| `building_posthumous_employment_center` | `regular` | `common/buildings/pif_01_pop_assembly_buildings_building_posthumous_employment_center.txt` |
| `building_automation_technician_1` | `regular` | `common/buildings/pif_01_pop_assembly_buildings_building_automation_technician_1.txt` |
| `building_automation_technician_2` | `regular` | `common/buildings/pif_01_pop_assembly_buildings_building_automation_technician_2.txt` |
| `building_automation_miner_1` | `regular` | `common/buildings/pif_01_pop_assembly_buildings_building_automation_miner_1.txt` |
| `building_automation_miner_2` | `regular` | `common/buildings/pif_01_pop_assembly_buildings_building_automation_miner_2.txt` |
| `building_automation_farmer_1` | `regular` | `common/buildings/pif_01_pop_assembly_buildings_building_automation_farmer_1.txt` |
| `building_automation_farmer_2` | `regular` | `common/buildings/pif_01_pop_assembly_buildings_building_automation_farmer_2.txt` |
| `building_automation_1` | `regular` | `common/buildings/pif_01_pop_assembly_buildings_building_automation_1.txt` |
| `building_automation_2` | `regular` | `common/buildings/pif_01_pop_assembly_buildings_building_automation_2.txt` |

### `buildings/02_government_buildings.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `building_noble_estates` | `regular` | `common/buildings/pif_02_government_buildings_building_noble_estates.txt` |
| `building_slave_processing` | `regular` | `common/buildings/pif_02_government_buildings_building_slave_processing.txt` |
| `building_precinct_house` | `regular` | `common/buildings/pif_02_government_buildings_building_precinct_house.txt` |
| `building_hall_judgment` | `regular` | `common/buildings/pif_02_government_buildings_building_hall_judgment.txt` |
| `building_state_academy` | `regular` | `common/buildings/pif_02_government_buildings_building_state_academy.txt` |
| `building_center_of_guidance` | `regular` | `common/buildings/pif_02_government_buildings_building_center_of_guidance.txt` |
| `building_sentinel_posts` | `regular` | `common/buildings/pif_02_government_buildings_building_sentinel_posts.txt` |
| `building_order_keep` | `regular` | `common/buildings/pif_02_government_buildings_building_order_keep.txt` |
| `building_order_castle` | `regular` | `common/buildings/pif_02_government_buildings_building_order_castle.txt` |
| `building_psi_corps` | `regular` | `common/buildings/pif_02_government_buildings_building_psi_corps.txt` |
| `building_embassy` | `regular` | `common/buildings/pif_02_government_buildings_building_embassy.txt` |
| `building_grand_embassy` | `regular` | `common/buildings/pif_02_government_buildings_building_grand_embassy.txt` |
| `building_gaiaseeders_1` | `regular` | `common/buildings/pif_02_government_buildings_building_gaiaseeders_1.txt` |
| `building_gaiaseeders_2` | `regular` | `common/buildings/pif_02_government_buildings_building_gaiaseeders_2.txt` |
| `building_gaiaseeders_3` | `regular` | `common/buildings/pif_02_government_buildings_building_gaiaseeders_3.txt` |
| `building_gaiaseeders_4` | `regular` | `common/buildings/pif_02_government_buildings_building_gaiaseeders_4.txt` |
| `building_gaiaseeders_pc_gaia` | `regular` | `common/buildings/pif_02_government_buildings_building_gaiaseeders_pc_gaia.txt` |
| `building_volcanic_forge_1` | `regular` | `common/buildings/pif_02_government_buildings_building_volcanic_forge_1.txt` |
| `building_volcanic_forge_2` | `regular` | `common/buildings/pif_02_government_buildings_building_volcanic_forge_2.txt` |

### `buildings/03_resource_buildings.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `building_hydroponics_farm` | `regular` | `common/buildings/pif_03_resource_buildings_building_hydroponics_farm.txt` |
| `building_food_processing_facility` | `regular` | `common/buildings/pif_03_resource_buildings_building_food_processing_facility.txt` |
| `building_food_processing_center` | `regular` | `common/buildings/pif_03_resource_buildings_building_food_processing_center.txt` |
| `building_farming_districts_1` | `regular` | `common/buildings/pif_03_resource_buildings_building_farming_districts_1.txt` |
| `building_farming_districts_2` | `regular` | `common/buildings/pif_03_resource_buildings_building_farming_districts_2.txt` |
| `building_farming_districts_3` | `regular` | `common/buildings/pif_03_resource_buildings_building_farming_districts_3.txt` |
| `building_farming_districts_4` | `regular` | `common/buildings/pif_03_resource_buildings_building_farming_districts_4.txt` |
| `building_baol_organic_plant` | `regular` | `common/buildings/pif_03_resource_buildings_building_baol_organic_plant.txt` |
| `building_mine_generic` | `regular` | `common/buildings/pif_03_resource_buildings_building_mine_generic.txt` |
| `building_mineral_purification_plant` | `regular` | `common/buildings/pif_03_resource_buildings_building_mineral_purification_plant.txt` |
| `building_mineral_purification_hub` | `regular` | `common/buildings/pif_03_resource_buildings_building_mineral_purification_hub.txt` |
| `building_mining_districts_1` | `regular` | `common/buildings/pif_03_resource_buildings_building_mining_districts_1.txt` |
| `building_mining_districts_2` | `regular` | `common/buildings/pif_03_resource_buildings_building_mining_districts_2.txt` |
| `building_mining_districts_3` | `regular` | `common/buildings/pif_03_resource_buildings_building_mining_districts_3.txt` |
| `building_mining_districts_4` | `regular` | `common/buildings/pif_03_resource_buildings_building_mining_districts_4.txt` |
| `building_generator_generic` | `regular` | `common/buildings/pif_03_resource_buildings_building_generator_generic.txt` |
| `building_energy_grid` | `regular` | `common/buildings/pif_03_resource_buildings_building_energy_grid.txt` |
| `building_energy_nexus` | `regular` | `common/buildings/pif_03_resource_buildings_building_energy_nexus.txt` |
| `building_generator_districts_1` | `regular` | `common/buildings/pif_03_resource_buildings_building_generator_districts_1.txt` |
| `building_generator_districts_2` | `regular` | `common/buildings/pif_03_resource_buildings_building_generator_districts_2.txt` |
| `building_generator_districts_3` | `regular` | `common/buildings/pif_03_resource_buildings_building_generator_districts_3.txt` |
| `building_generator_districts_4` | `regular` | `common/buildings/pif_03_resource_buildings_building_generator_districts_4.txt` |
| `building_resource_silo` | `regular` | `common/buildings/pif_03_resource_buildings_building_resource_silo.txt` |
| `building_bio_reactor` | `regular` | `common/buildings/pif_03_resource_buildings_building_bio_reactor.txt` |
| `building_bio_reactor_2` | `regular` | `common/buildings/pif_03_resource_buildings_building_bio_reactor_2.txt` |

### `buildings/04_manufacturing_buildings.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `building_foundry_1` | `regular` | `common/buildings/pif_04_manufacturing_buildings_building_foundry_1.txt` |
| `building_foundry_2` | `regular` | `common/buildings/pif_04_manufacturing_buildings_building_foundry_2.txt` |
| `building_foundry_3` | `regular` | `common/buildings/pif_04_manufacturing_buildings_building_foundry_3.txt` |
| `building_factory_1` | `regular` | `common/buildings/pif_04_manufacturing_buildings_building_factory_1.txt` |
| `building_factory_2` | `regular` | `common/buildings/pif_04_manufacturing_buildings_building_factory_2.txt` |
| `building_factory_3` | `regular` | `common/buildings/pif_04_manufacturing_buildings_building_factory_3.txt` |
| `building_refinery` | `regular` | `common/buildings/pif_04_manufacturing_buildings_building_refinery.txt` |
| `building_chemical_plant` | `regular` | `common/buildings/pif_04_manufacturing_buildings_building_chemical_plant.txt` |
| `building_crystal_plant` | `regular` | `common/buildings/pif_04_manufacturing_buildings_building_crystal_plant.txt` |
| `building_nanite_transmuter` | `regular` | `common/buildings/pif_04_manufacturing_buildings_building_nanite_transmuter.txt` |
| `building_ministry_production` | `regular` | `common/buildings/pif_04_manufacturing_buildings_building_ministry_production.txt` |
| `building_production_center` | `regular` | `common/buildings/pif_04_manufacturing_buildings_building_production_center.txt` |
| `building_coordinated_fulfillment_center_1` | `regular` | `common/buildings/pif_04_manufacturing_buildings_building_coordinated_fulfillment_center_1.txt` |
| `building_coordinated_fulfillment_center_2` | `regular` | `common/buildings/pif_04_manufacturing_buildings_building_coordinated_fulfillment_center_2.txt` |
| `building_archaeo_refinery` | `regular` | `common/buildings/pif_04_manufacturing_buildings_building_archaeo_refinery.txt` |
| `building_foundry_upkeep_1` | `regular` | `common/buildings/pif_04_manufacturing_buildings_building_foundry_upkeep_1.txt` |
| `building_foundry_efficiency_1` | `regular` | `common/buildings/pif_04_manufacturing_buildings_building_foundry_efficiency_1.txt` |
| `building_factory_upkeep_1` | `regular` | `common/buildings/pif_04_manufacturing_buildings_building_factory_upkeep_1.txt` |
| `building_factory_efficiency_1` | `regular` | `common/buildings/pif_04_manufacturing_buildings_building_factory_efficiency_1.txt` |
| `building_offworld_expedition_hub` | `regular` | `common/buildings/pif_04_manufacturing_buildings_building_offworld_expedition_hub.txt` |

### `buildings/05_research_buildings.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `building_research_lab_1` | `regular` | `common/buildings/pif_05_research_buildings_building_research_lab_1.txt` |
| `building_research_lab_2` | `regular` | `common/buildings/pif_05_research_buildings_building_research_lab_2.txt` |
| `building_research_lab_3` | `regular` | `common/buildings/pif_05_research_buildings_building_research_lab_3.txt` |
| `building_institute` | `regular` | `common/buildings/pif_05_research_buildings_building_institute.txt` |
| `building_supercomputer` | `regular` | `common/buildings/pif_05_research_buildings_building_supercomputer.txt` |
| `building_shroud_observatory_1` | `regular` | `common/buildings/pif_05_research_buildings_building_shroud_observatory_1.txt` |
| `building_shroud_observatory_2` | `regular` | `common/buildings/pif_05_research_buildings_building_shroud_observatory_2.txt` |
| `building_shroud_observatory_3` | `regular` | `common/buildings/pif_05_research_buildings_building_shroud_observatory_3.txt` |
| `building_archaeostudies_faculty` | `regular` | `common/buildings/pif_05_research_buildings_building_archaeostudies_faculty.txt` |
| `building_vultaum_reality_computer` | `regular` | `common/buildings/pif_05_research_buildings_building_vultaum_reality_computer.txt` |
| `building_physics_lab_1` | `regular` | `common/buildings/pif_05_research_buildings_building_physics_lab_1.txt` |
| `building_physics_lab_2` | `regular` | `common/buildings/pif_05_research_buildings_building_physics_lab_2.txt` |
| `building_physics_lab_3` | `regular` | `common/buildings/pif_05_research_buildings_building_physics_lab_3.txt` |
| `building_biolab_1` | `regular` | `common/buildings/pif_05_research_buildings_building_biolab_1.txt` |
| `building_biolab_2` | `regular` | `common/buildings/pif_05_research_buildings_building_biolab_2.txt` |
| `building_biolab_3` | `regular` | `common/buildings/pif_05_research_buildings_building_biolab_3.txt` |
| `building_engineering_facility_1` | `regular` | `common/buildings/pif_05_research_buildings_building_engineering_facility_1.txt` |
| `building_engineering_facility_2` | `regular` | `common/buildings/pif_05_research_buildings_building_engineering_facility_2.txt` |
| `building_engineering_facility_3` | `regular` | `common/buildings/pif_05_research_buildings_building_engineering_facility_3.txt` |
| `building_ranger_lodge` | `regular` | `common/buildings/pif_05_research_buildings_building_ranger_lodge.txt` |
| `building_research_upkeep_1` | `regular` | `common/buildings/pif_05_research_buildings_building_research_upkeep_1.txt` |
| `building_research_efficiency_1` | `regular` | `common/buildings/pif_05_research_buildings_building_research_efficiency_1.txt` |

### `buildings/06_trade_buildings.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `building_commercial_zone` | `regular` | `common/buildings/pif_06_trade_buildings_building_commercial_zone.txt` |
| `building_commercial_megaplex` | `regular` | `common/buildings/pif_06_trade_buildings_building_commercial_megaplex.txt` |
| `building_galactic_stock_exchange` | `regular` | `common/buildings/pif_06_trade_buildings_building_galactic_stock_exchange.txt` |
| `building_maintenance_depot` | `regular` | `common/buildings/pif_06_trade_buildings_building_maintenance_depot.txt` |

### `buildings/07_amenity_buildings.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `building_luxury_residence` | `regular` | `common/buildings/pif_07_amenity_buildings_building_luxury_residence.txt` |
| `building_paradise_dome` | `regular` | `common/buildings/pif_07_amenity_buildings_building_paradise_dome.txt` |
| `building_communal_housing` | `regular` | `common/buildings/pif_07_amenity_buildings_building_communal_housing.txt` |
| `building_communal_housing_large` | `regular` | `common/buildings/pif_07_amenity_buildings_building_communal_housing_large.txt` |
| `building_drone_storage` | `regular` | `common/buildings/pif_07_amenity_buildings_building_drone_storage.txt` |
| `building_drone_megastorage` | `regular` | `common/buildings/pif_07_amenity_buildings_building_drone_megastorage.txt` |
| `building_hive_warren` | `regular` | `common/buildings/pif_07_amenity_buildings_building_hive_warren.txt` |
| `building_expanded_warren` | `regular` | `common/buildings/pif_07_amenity_buildings_building_expanded_warren.txt` |
| `building_holo_theatres` | `regular` | `common/buildings/pif_07_amenity_buildings_building_holo_theatres.txt` |
| `building_hyper_entertainment_forum` | `regular` | `common/buildings/pif_07_amenity_buildings_building_hyper_entertainment_forum.txt` |
| `building_medical_1` | `regular` | `common/buildings/pif_07_amenity_buildings_building_medical_1.txt` |
| `building_medical_2` | `regular` | `common/buildings/pif_07_amenity_buildings_building_medical_2.txt` |
| `building_medical_3` | `regular` | `common/buildings/pif_07_amenity_buildings_building_medical_3.txt` |
| `building_overseer_homes` | `regular` | `common/buildings/pif_07_amenity_buildings_building_overseer_homes.txt` |
| `building_toxic_bath` | `regular` | `common/buildings/pif_07_amenity_buildings_building_toxic_bath.txt` |
| `building_toxic_bath_hive` | `regular` | `common/buildings/pif_07_amenity_buildings_building_toxic_bath_hive.txt` |
| `building_toxic_bath_machine` | `regular` | `common/buildings/pif_07_amenity_buildings_building_toxic_bath_machine.txt` |

### `buildings/08_unity_buildings.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `building_autochthon_monument` | `regular` | `common/buildings/pif_08_unity_buildings_building_autochthon_monument.txt` |
| `building_heritage_site` | `regular` | `common/buildings/pif_08_unity_buildings_building_heritage_site.txt` |
| `building_hypercomms_forum` | `regular` | `common/buildings/pif_08_unity_buildings_building_hypercomms_forum.txt` |
| `building_bureaucratic_1` | `regular` | `common/buildings/pif_08_unity_buildings_building_bureaucratic_1.txt` |
| `building_bureaucratic_2` | `regular` | `common/buildings/pif_08_unity_buildings_building_bureaucratic_2.txt` |
| `building_bureaucratic_3` | `regular` | `common/buildings/pif_08_unity_buildings_building_bureaucratic_3.txt` |
| `building_temple` | `regular` | `common/buildings/pif_08_unity_buildings_building_temple.txt` |
| `building_holotemple` | `regular` | `common/buildings/pif_08_unity_buildings_building_holotemple.txt` |
| `building_sacred_nexus` | `regular` | `common/buildings/pif_08_unity_buildings_building_sacred_nexus.txt` |
| `building_uplink_node` | `regular` | `common/buildings/pif_08_unity_buildings_building_uplink_node.txt` |
| `building_network_junction` | `regular` | `common/buildings/pif_08_unity_buildings_building_network_junction.txt` |
| `building_system_conflux` | `regular` | `common/buildings/pif_08_unity_buildings_building_system_conflux.txt` |
| `building_hive_node` | `regular` | `common/buildings/pif_08_unity_buildings_building_hive_node.txt` |
| `building_hive_cluster` | `regular` | `common/buildings/pif_08_unity_buildings_building_hive_cluster.txt` |
| `building_hive_confluence` | `regular` | `common/buildings/pif_08_unity_buildings_building_hive_confluence.txt` |
| `building_sacrificial_temple_1` | `regular` | `common/buildings/pif_08_unity_buildings_building_sacrificial_temple_1.txt` |
| `building_sacrificial_temple_2` | `regular` | `common/buildings/pif_08_unity_buildings_building_sacrificial_temple_2.txt` |
| `building_sacrificial_temple_3` | `regular` | `common/buildings/pif_08_unity_buildings_building_sacrificial_temple_3.txt` |
| `building_galactic_memorial_1` | `regular` | `common/buildings/pif_08_unity_buildings_building_galactic_memorial_1.txt` |
| `building_galactic_memorial_2` | `regular` | `common/buildings/pif_08_unity_buildings_building_galactic_memorial_2.txt` |
| `building_galactic_memorial_3` | `regular` | `common/buildings/pif_08_unity_buildings_building_galactic_memorial_3.txt` |
| `building_simulation_1` | `regular` | `common/buildings/pif_08_unity_buildings_building_simulation_1.txt` |
| `building_simulation_2` | `regular` | `common/buildings/pif_08_unity_buildings_building_simulation_2.txt` |
| `building_simulation_3` | `regular` | `common/buildings/pif_08_unity_buildings_building_simulation_3.txt` |
| `building_corporate_monument` | `regular` | `common/buildings/pif_08_unity_buildings_building_corporate_monument.txt` |
| `building_corporate_site` | `regular` | `common/buildings/pif_08_unity_buildings_building_corporate_site.txt` |
| `building_corporate_forum` | `regular` | `common/buildings/pif_08_unity_buildings_building_corporate_forum.txt` |
| `building_sensorium_1` | `regular` | `common/buildings/pif_08_unity_buildings_building_sensorium_1.txt` |
| `building_sensorium_2` | `regular` | `common/buildings/pif_08_unity_buildings_building_sensorium_2.txt` |
| `building_sensorium_3` | `regular` | `common/buildings/pif_08_unity_buildings_building_sensorium_3.txt` |
| `building_autocurating_vault` | `regular` | `common/buildings/pif_08_unity_buildings_building_autocurating_vault.txt` |
| `building_citadel_of_faith` | `regular` | `common/buildings/pif_08_unity_buildings_building_citadel_of_faith.txt` |
| `building_corporate_vault` | `regular` | `common/buildings/pif_08_unity_buildings_building_corporate_vault.txt` |
| `building_alpha_hub` | `regular` | `common/buildings/pif_08_unity_buildings_building_alpha_hub.txt` |
| `building_organic_sanctuary` | `regular` | `common/buildings/pif_08_unity_buildings_building_organic_sanctuary.txt` |
| `building_organic_paradise` | `regular` | `common/buildings/pif_08_unity_buildings_building_organic_paradise.txt` |
| `building_trophy_vault` | `regular` | `common/buildings/pif_08_unity_buildings_building_trophy_vault.txt` |
| `building_league_offices` | `regular` | `common/buildings/pif_08_unity_buildings_building_league_offices.txt` |

### `buildings/09_army_buildings.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `building_military_academy` | `regular` | `common/buildings/pif_09_army_buildings_building_military_academy.txt` |
| `building_dread_encampment` | `regular` | `common/buildings/pif_09_army_buildings_building_dread_encampment.txt` |
| `building_stronghold` | `regular` | `common/buildings/pif_09_army_buildings_building_stronghold.txt` |
| `building_fortress` | `regular` | `common/buildings/pif_09_army_buildings_building_fortress.txt` |
| `building_planetary_shield_generator` | `regular` | `common/buildings/pif_09_army_buildings_building_planetary_shield_generator.txt` |

### `buildings/10_deposit_buildings.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `building_mote_harvesters` | `regular` | `common/buildings/pif_10_deposit_buildings_building_mote_harvesters.txt` |
| `building_gas_extractors` | `regular` | `common/buildings/pif_10_deposit_buildings_building_gas_extractors.txt` |
| `building_crystal_mines` | `regular` | `common/buildings/pif_10_deposit_buildings_building_crystal_mines.txt` |
| `building_betharian_power_plant` | `regular` | `common/buildings/pif_10_deposit_buildings_building_betharian_power_plant.txt` |
| `building_xeno_zoo` | `regular` | `common/buildings/pif_10_deposit_buildings_building_xeno_zoo.txt` |

### `buildings/11_primitive_buildings.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `building_crude_huts` | `capital` | `common/buildings/pif_11_primitive_buildings_building_crude_huts.txt` |
| `building_primitive_dwellings` | `regular` | `common/buildings/pif_11_primitive_buildings_building_primitive_dwellings.txt` |
| `building_stone_palace` | `capital` | `common/buildings/pif_11_primitive_buildings_building_stone_palace.txt` |
| `building_primitive_factory` | `regular` | `common/buildings/pif_11_primitive_buildings_building_primitive_factory.txt` |
| `building_primitive_offices` | `regular` | `common/buildings/pif_11_primitive_buildings_building_primitive_offices.txt` |
| `building_primitive_research` | `regular` | `common/buildings/pif_11_primitive_buildings_building_primitive_research.txt` |
| `building_primitive_mine` | `regular` | `common/buildings/pif_11_primitive_buildings_building_primitive_mine.txt` |
| `building_primitive_power_plant` | `regular` | `common/buildings/pif_11_primitive_buildings_building_primitive_power_plant.txt` |
| `building_primitive_farm` | `regular` | `common/buildings/pif_11_primitive_buildings_building_primitive_farm.txt` |
| `building_primitive_capital` | `capital` | `common/buildings/pif_11_primitive_buildings_building_primitive_capital.txt` |
| `building_urban_dwellings` | `regular` | `common/buildings/pif_11_primitive_buildings_building_urban_dwellings.txt` |
| `building_pre_ftl_radio_telescope` | `regular` | `common/buildings/pif_11_primitive_buildings_building_pre_ftl_radio_telescope.txt` |
| `building_hive_crude_huts` | `capital` | `common/buildings/pif_11_primitive_buildings_building_hive_crude_huts.txt` |
| `building_hive_primitive_dwellings` | `regular` | `common/buildings/pif_11_primitive_buildings_building_hive_primitive_dwellings.txt` |
| `building_hive_stone_palace` | `capital` | `common/buildings/pif_11_primitive_buildings_building_hive_stone_palace.txt` |
| `building_hive_primitive_factory` | `regular` | `common/buildings/pif_11_primitive_buildings_building_hive_primitive_factory.txt` |
| `building_hive_primitive_mine` | `regular` | `common/buildings/pif_11_primitive_buildings_building_hive_primitive_mine.txt` |
| `building_hive_primitive_power_plant` | `regular` | `common/buildings/pif_11_primitive_buildings_building_hive_primitive_power_plant.txt` |
| `building_hive_primitive_farm` | `regular` | `common/buildings/pif_11_primitive_buildings_building_hive_primitive_farm.txt` |
| `building_hive_primitive_capital` | `capital` | `common/buildings/pif_11_primitive_buildings_building_hive_primitive_capital.txt` |
| `building_hive_urban_dwellings` | `regular` | `common/buildings/pif_11_primitive_buildings_building_hive_urban_dwellings.txt` |
| `building_hive_primitive_node` | `regular` | `common/buildings/pif_11_primitive_buildings_building_hive_primitive_node.txt` |
| `building_machine_primitive_node` | `regular` | `common/buildings/pif_11_primitive_buildings_building_machine_primitive_node.txt` |
| `building_primitive_clinic` | `regular` | `common/buildings/pif_11_primitive_buildings_building_primitive_clinic.txt` |
| `building_solarpunk_gaiaseeder` | `regular` | `common/buildings/pif_11_primitive_buildings_building_solarpunk_gaiaseeder.txt` |
| `building_solarpunk_ranger_lodge` | `regular` | `common/buildings/pif_11_primitive_buildings_building_solarpunk_ranger_lodge.txt` |
| `building_solarpunk_sapling` | `regular` | `common/buildings/pif_11_primitive_buildings_building_solarpunk_sapling.txt` |
| `building_solarpunk_organic_paradise` | `regular` | `common/buildings/pif_11_primitive_buildings_building_solarpunk_organic_paradise.txt` |

### `buildings/12_event_buildings.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `building_junkheap` | `capital` | `common/buildings/pif_12_event_buildings_building_junkheap.txt` |
| `building_akx_worm_3` | `regular` | `common/buildings/pif_12_event_buildings_building_akx_worm_3.txt` |
| `building_great_pyramid` | `regular` | `common/buildings/pif_12_event_buildings_building_great_pyramid.txt` |
| `building_artist_patron` | `regular` | `common/buildings/pif_12_event_buildings_building_artist_patron.txt` |
| `building_waste_reprocessing_center` | `regular` | `common/buildings/pif_12_event_buildings_building_waste_reprocessing_center.txt` |
| `building_nuumismatic_shrine` | `regular` | `common/buildings/pif_12_event_buildings_building_nuumismatic_shrine.txt` |
| `building_crystal_plant_2` | `regular` | `common/buildings/pif_12_event_buildings_building_crystal_plant_2.txt` |
| `building_zroni_equilibrator` | `regular` | `common/buildings/pif_12_event_buildings_building_zroni_equilibrator.txt` |
| `building_composer_sanctum` | `regular` | `common/buildings/pif_12_event_buildings_building_composer_sanctum.txt` |
| `building_eater_sanctum` | `regular` | `common/buildings/pif_12_event_buildings_building_eater_sanctum.txt` |
| `building_instrument_sanctum` | `regular` | `common/buildings/pif_12_event_buildings_building_instrument_sanctum.txt` |
| `building_whisperers_sanctum` | `regular` | `common/buildings/pif_12_event_buildings_building_whisperers_sanctum.txt` |

### `buildings/13_fallen_empire_buildings.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `building_ancient_control_center` | `capital` | `common/buildings/pif_13_fallen_empire_buildings_building_ancient_control_center.txt` |
| `building_ancient_hive_capital` | `capital` | `common/buildings/pif_13_fallen_empire_buildings_building_ancient_hive_capital.txt` |
| `building_ancient_palace` | `capital` | `common/buildings/pif_13_fallen_empire_buildings_building_ancient_palace.txt` |
| `building_fe_xeno_zoo` | `capital` | `common/buildings/pif_13_fallen_empire_buildings_building_fe_xeno_zoo.txt` |
| `building_hab_fe_capital` | `capital` | `common/buildings/pif_13_fallen_empire_buildings_building_hab_fe_capital.txt` |
| `building_master_archive` | `regular` | `common/buildings/pif_13_fallen_empire_buildings_building_master_archive.txt` |
| `building_empyrean_shrine` | `regular` | `common/buildings/pif_13_fallen_empire_buildings_building_empyrean_shrine.txt` |
| `building_ancient_cryo_chamber` | `regular` | `common/buildings/pif_13_fallen_empire_buildings_building_ancient_cryo_chamber.txt` |
| `building_affluence_emporium` | `regular` | `common/buildings/pif_13_fallen_empire_buildings_building_affluence_emporium.txt` |
| `building_affluence_center` | `regular` | `common/buildings/pif_13_fallen_empire_buildings_building_affluence_center.txt` |
| `building_nourishment_complex` | `regular` | `common/buildings/pif_13_fallen_empire_buildings_building_nourishment_complex.txt` |
| `building_nourishment_center` | `regular` | `common/buildings/pif_13_fallen_empire_buildings_building_nourishment_center.txt` |
| `building_dimensional_replicator` | `regular` | `common/buildings/pif_13_fallen_empire_buildings_building_dimensional_replicator.txt` |
| `building_dimensional_fabricator` | `regular` | `common/buildings/pif_13_fallen_empire_buildings_building_dimensional_fabricator.txt` |
| `building_class_3_singularity` | `regular` | `common/buildings/pif_13_fallen_empire_buildings_building_class_3_singularity.txt` |
| `building_class_4_singularity` | `regular` | `common/buildings/pif_13_fallen_empire_buildings_building_class_4_singularity.txt` |
| `building_micro_forge` | `regular` | `common/buildings/pif_13_fallen_empire_buildings_building_micro_forge.txt` |
| `building_nano_forge` | `regular` | `common/buildings/pif_13_fallen_empire_buildings_building_nano_forge.txt` |
| `building_fe_sky_dome` | `regular` | `common/buildings/pif_13_fallen_empire_buildings_building_fe_sky_dome.txt` |
| `building_fe_dome` | `regular` | `common/buildings/pif_13_fallen_empire_buildings_building_fe_dome.txt` |
| `building_fe_fortress` | `regular` | `common/buildings/pif_13_fallen_empire_buildings_building_fe_fortress.txt` |
| `building_fe_stronghold` | `regular` | `common/buildings/pif_13_fallen_empire_buildings_building_fe_stronghold.txt` |
| `building_fe_administration_1` | `regular` | `common/buildings/pif_13_fallen_empire_buildings_building_fe_administration_1.txt` |
| `building_fe_administration_2` | `regular` | `common/buildings/pif_13_fallen_empire_buildings_building_fe_administration_2.txt` |
| `building_fe_administration_hive_1` | `regular` | `common/buildings/pif_13_fallen_empire_buildings_building_fe_administration_hive_1.txt` |
| `building_fe_administration_hive_2` | `regular` | `common/buildings/pif_13_fallen_empire_buildings_building_fe_administration_hive_2.txt` |
| `building_fe_administration_machine_1` | `regular` | `common/buildings/pif_13_fallen_empire_buildings_building_fe_administration_machine_1.txt` |
| `building_fe_administration_machine_2` | `regular` | `common/buildings/pif_13_fallen_empire_buildings_building_fe_administration_machine_2.txt` |
| `building_fe_temple_1` | `regular` | `common/buildings/pif_13_fallen_empire_buildings_building_fe_temple_1.txt` |
| `building_fe_temple_2` | `regular` | `common/buildings/pif_13_fallen_empire_buildings_building_fe_temple_2.txt` |
| `building_fe_assembly_1` | `regular` | `common/buildings/pif_13_fallen_empire_buildings_building_fe_assembly_1.txt` |
| `building_fe_assembly_2` | `regular` | `common/buildings/pif_13_fallen_empire_buildings_building_fe_assembly_2.txt` |
| `building_fe_clinic_1` | `regular` | `common/buildings/pif_13_fallen_empire_buildings_building_fe_clinic_1.txt` |
| `building_fe_clinic_2` | `regular` | `common/buildings/pif_13_fallen_empire_buildings_building_fe_clinic_2.txt` |
| `building_fe_security_1` | `regular` | `common/buildings/pif_13_fallen_empire_buildings_building_fe_security_1.txt` |
| `building_fe_security_2` | `regular` | `common/buildings/pif_13_fallen_empire_buildings_building_fe_security_2.txt` |
| `building_fe_market_1` | `regular` | `common/buildings/pif_13_fallen_empire_buildings_building_fe_market_1.txt` |
| `building_fe_market_2` | `regular` | `common/buildings/pif_13_fallen_empire_buildings_building_fe_market_2.txt` |
| `building_fe_silo_1` | `regular` | `common/buildings/pif_13_fallen_empire_buildings_building_fe_silo_1.txt` |
| `building_fe_silo_2` | `regular` | `common/buildings/pif_13_fallen_empire_buildings_building_fe_silo_2.txt` |
| `building_fe_entertainment_1` | `regular` | `common/buildings/pif_13_fallen_empire_buildings_building_fe_entertainment_1.txt` |
| `building_fe_entertainment_2` | `regular` | `common/buildings/pif_13_fallen_empire_buildings_building_fe_entertainment_2.txt` |
| `building_fe_lab_1` | `regular` | `common/buildings/pif_13_fallen_empire_buildings_building_fe_lab_1.txt` |
| `building_fe_lab_2` | `regular` | `common/buildings/pif_13_fallen_empire_buildings_building_fe_lab_2.txt` |
| `building_fe_mine_1` | `regular` | `common/buildings/pif_13_fallen_empire_buildings_building_fe_mine_1.txt` |
| `building_fe_mine_2` | `regular` | `common/buildings/pif_13_fallen_empire_buildings_building_fe_mine_2.txt` |

### `buildings/14_branch_office_buildings.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `building_private_mining_consortium` | `branch` | `common/buildings/pif_14_branch_office_buildings_building_private_mining_consortium.txt` |
| `building_food_conglomerate` | `branch` | `common/buildings/pif_14_branch_office_buildings_building_food_conglomerate.txt` |
| `building_virtual_entertainment_studios` | `branch` | `common/buildings/pif_14_branch_office_buildings_building_virtual_entertainment_studios.txt` |
| `building_private_shipyards` | `branch` | `common/buildings/pif_14_branch_office_buildings_building_private_shipyards.txt` |
| `building_military_contractors` | `branch` | `common/buildings/pif_14_branch_office_buildings_building_military_contractors.txt` |
| `building_industrial_subsidiary` | `branch` | `common/buildings/pif_14_branch_office_buildings_building_industrial_subsidiary.txt` |
| `building_public_relations_office` | `branch` | `common/buildings/pif_14_branch_office_buildings_building_public_relations_office.txt` |
| `building_private_research_initiative` | `branch` | `common/buildings/pif_14_branch_office_buildings_building_private_research_initiative.txt` |
| `building_amusement_megaplex` | `branch` | `common/buildings/pif_14_branch_office_buildings_building_amusement_megaplex.txt` |
| `building_commercial_forum` | `branch` | `common/buildings/pif_14_branch_office_buildings_building_commercial_forum.txt` |
| `building_corporate_embassy` | `branch` | `common/buildings/pif_14_branch_office_buildings_building_corporate_embassy.txt` |
| `building_private_security` | `branch` | `common/buildings/pif_14_branch_office_buildings_building_private_security.txt` |
| `building_wildcat_miners` | `branch` | `common/buildings/pif_14_branch_office_buildings_building_wildcat_miners.txt` |
| `building_bio_reprocessing_facilities` | `branch` | `common/buildings/pif_14_branch_office_buildings_building_bio_reprocessing_facilities.txt` |
| `building_underground_chemists` | `branch` | `common/buildings/pif_14_branch_office_buildings_building_underground_chemists.txt` |
| `building_wrecking_yards` | `branch` | `common/buildings/pif_14_branch_office_buildings_building_wrecking_yards.txt` |
| `building_pirate_haven` | `branch` | `common/buildings/pif_14_branch_office_buildings_building_pirate_haven.txt` |
| `building_underground_clubs` | `branch` | `common/buildings/pif_14_branch_office_buildings_building_underground_clubs.txt` |
| `building_syndicate_outreach_office` | `branch` | `common/buildings/pif_14_branch_office_buildings_building_syndicate_outreach_office.txt` |
| `building_illicit_research_labs` | `branch` | `common/buildings/pif_14_branch_office_buildings_building_illicit_research_labs.txt` |
| `building_smuggling_rings` | `branch` | `common/buildings/pif_14_branch_office_buildings_building_smuggling_rings.txt` |
| `building_disinformation_center` | `branch` | `common/buildings/pif_14_branch_office_buildings_building_disinformation_center.txt` |
| `building_subversive_shrine` | `branch` | `common/buildings/pif_14_branch_office_buildings_building_subversive_shrine.txt` |
| `building_temple_of_prosperity` | `branch` | `common/buildings/pif_14_branch_office_buildings_building_temple_of_prosperity.txt` |
| `building_executive_retreat` | `branch` | `common/buildings/pif_14_branch_office_buildings_building_executive_retreat.txt` |
| `building_xeno_tourism_agency` | `branch` | `common/buildings/pif_14_branch_office_buildings_building_xeno_tourism_agency.txt` |
| `building_imperial_concession_port` | `branch` | `common/buildings/pif_14_branch_office_buildings_building_imperial_concession_port.txt` |
| `building_knightly_theme_park` | `branch` | `common/buildings/pif_14_branch_office_buildings_building_knightly_theme_park.txt` |
| `building_corporate_clinics` | `branch` | `common/buildings/pif_14_branch_office_buildings_building_corporate_clinics.txt` |
| `building_augmentation_bazaars_branch` | `branch` | `common/buildings/pif_14_branch_office_buildings_building_augmentation_bazaars_branch.txt` |
| `building_ai_emporium` | `branch` | `common/buildings/pif_14_branch_office_buildings_building_ai_emporium.txt` |
| `building_clear_thought_clinic` | `branch` | `common/buildings/pif_14_branch_office_buildings_building_clear_thought_clinic.txt` |
| `building_carceral_test_facility` | `branch` | `common/buildings/pif_14_branch_office_buildings_building_carceral_test_facility.txt` |
| `building_psionic_offices` | `branch` | `common/buildings/pif_14_branch_office_buildings_building_psionic_offices.txt` |
| `building_living_metal_clinic` | `branch` | `common/buildings/pif_14_branch_office_buildings_building_living_metal_clinic.txt` |

### `buildings/15_overlord_holdings.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `holding_garrison` | `holding` | `common/buildings/pif_15_overlord_holdings_holding_garrison.txt` |
| `holding_orbital_assembly_complex` | `holding` | `common/buildings/pif_15_overlord_holdings_holding_orbital_assembly_complex.txt` |
| `holding_propaganda_office` | `holding` | `common/buildings/pif_15_overlord_holdings_holding_propaganda_office.txt` |
| `holding_satellite_campus` | `holding` | `common/buildings/pif_15_overlord_holdings_holding_satellite_campus.txt` |
| `holding_emporium` | `holding` | `common/buildings/pif_15_overlord_holdings_holding_emporium.txt` |
| `holding_aid_agency` | `holding` | `common/buildings/pif_15_overlord_holdings_holding_aid_agency.txt` |
| `holding_energy_requisitorium` | `holding` | `common/buildings/pif_15_overlord_holdings_holding_energy_requisitorium.txt` |
| `holding_material_requisitorium` | `holding` | `common/buildings/pif_15_overlord_holdings_holding_material_requisitorium.txt` |
| `holding_produce_requisitorium` | `holding` | `common/buildings/pif_15_overlord_holdings_holding_produce_requisitorium.txt` |
| `holding_splinter_hive` | `holding` | `common/buildings/pif_15_overlord_holdings_holding_splinter_hive.txt` |
| `holding_distributed_processing` | `holding` | `common/buildings/pif_15_overlord_holdings_holding_distributed_processing.txt` |
| `holding_offspring_nest` | `holding` | `common/buildings/pif_15_overlord_holdings_holding_offspring_nest.txt` |
| `holding_offworld_foundry` | `holding` | `common/buildings/pif_15_overlord_holdings_holding_offworld_foundry.txt` |
| `holding_overlord_vigil_command` | `holding` | `common/buildings/pif_15_overlord_holdings_holding_overlord_vigil_command.txt` |
| `holding_parasitic_algorithms` | `holding` | `common/buildings/pif_15_overlord_holdings_holding_parasitic_algorithms.txt` |
| `holding_noble_vacation_homes` | `holding` | `common/buildings/pif_15_overlord_holdings_holding_noble_vacation_homes.txt` |
| `holding_dread_outpost` | `holding` | `common/buildings/pif_15_overlord_holdings_holding_dread_outpost.txt` |
| `holding_communal_housing_outreach` | `holding` | `common/buildings/pif_15_overlord_holdings_holding_communal_housing_outreach.txt` |
| `holding_idyllic_bloom` | `holding` | `common/buildings/pif_15_overlord_holdings_holding_idyllic_bloom.txt` |
| `holding_reemployment_center` | `holding` | `common/buildings/pif_15_overlord_holdings_holding_reemployment_center.txt` |
| `holding_recruitment_office` | `holding` | `common/buildings/pif_15_overlord_holdings_holding_recruitment_office.txt` |
| `holding_park_ranger_lodge` | `holding` | `common/buildings/pif_15_overlord_holdings_holding_park_ranger_lodge.txt` |
| `holding_tree_of_life_sapling` | `holding` | `common/buildings/pif_15_overlord_holdings_holding_tree_of_life_sapling.txt` |
| `holding_experimental_crater` | `holding` | `common/buildings/pif_15_overlord_holdings_holding_experimental_crater.txt` |
| `holding_organic_sanctuary` | `holding` | `common/buildings/pif_15_overlord_holdings_holding_organic_sanctuary.txt` |
| `holding_franchise_headquarters` | `holding` | `common/buildings/pif_15_overlord_holdings_holding_franchise_headquarters.txt` |
| `holding_sacrificial_shrine` | `holding` | `common/buildings/pif_15_overlord_holdings_holding_sacrificial_shrine.txt` |
| `holding_knight_commandery` | `holding` | `common/buildings/pif_15_overlord_holdings_holding_knight_commandery.txt` |
| `holding_transcendental_retreat` | `holding` | `common/buildings/pif_15_overlord_holdings_holding_transcendental_retreat.txt` |
| `holding_wilderness_glade` | `holding` | `common/buildings/pif_15_overlord_holdings_holding_wilderness_glade.txt` |

### `buildings/16_first_contact_buildings.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `building_low_tech_scrap_refinery` | `regular` | `common/buildings/pif_16_first_contact_buildings_building_low_tech_scrap_refinery.txt` |
| `building_low_tech_admin_hub` | `regular` | `common/buildings/pif_16_first_contact_buildings_building_low_tech_admin_hub.txt` |
| `building_low_tech_power_plant` | `regular` | `common/buildings/pif_16_first_contact_buildings_building_low_tech_power_plant.txt` |
| `building_low_tech_farm` | `regular` | `common/buildings/pif_16_first_contact_buildings_building_low_tech_farm.txt` |
| `building_low_tech_capital` | `capital` | `common/buildings/pif_16_first_contact_buildings_building_low_tech_capital.txt` |
| `building_low_tech_research_lab` | `regular` | `common/buildings/pif_16_first_contact_buildings_building_low_tech_research_lab.txt` |

### `buildings/17_paragon_buildings.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `building_paragon_memory_vaults` | `regular` | `common/buildings/pif_17_paragon_buildings_building_paragon_memory_vaults.txt` |
| `building_the_beholder` | `regular` | `common/buildings/pif_17_paragon_buildings_building_the_beholder.txt` |
| `building_contained_ecosphere` | `regular` | `common/buildings/pif_17_paragon_buildings_building_contained_ecosphere.txt` |

### `buildings/18_astral_planes_buildings.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `building_astral_siphon_1` | `regular` | `common/buildings/pif_18_astral_planes_buildings_building_astral_siphon_1.txt` |
| `building_astral_siphon_2` | `regular` | `common/buildings/pif_18_astral_planes_buildings_building_astral_siphon_2.txt` |
| `building_astral_siphon_3` | `regular` | `common/buildings/pif_18_astral_planes_buildings_building_astral_siphon_3.txt` |

### `buildings/19_cosmic_storm_buildings.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `building_storm_attraction_center` | `regular` | `common/buildings/pif_19_cosmic_storm_buildings_building_storm_attraction_center.txt` |
| `building_advanced_storm_attraction_center` | `regular` | `common/buildings/pif_19_cosmic_storm_buildings_building_advanced_storm_attraction_center.txt` |
| `building_storm_repellent_center` | `regular` | `common/buildings/pif_19_cosmic_storm_buildings_building_storm_repellent_center.txt` |
| `building_advanced_storm_repellent_center` | `regular` | `common/buildings/pif_19_cosmic_storm_buildings_building_advanced_storm_repellent_center.txt` |
| `building_storm_resistant_production` | `regular` | `common/buildings/pif_19_cosmic_storm_buildings_building_storm_resistant_production.txt` |
| `building_advanced_storm_resistant_production` | `regular` | `common/buildings/pif_19_cosmic_storm_buildings_building_advanced_storm_resistant_production.txt` |
| `building_adakkaria_patriotic_institute` | `regular` | `common/buildings/pif_19_cosmic_storm_buildings_building_adakkaria_patriotic_institute.txt` |
| `building_astrometeorology_observation_center` | `regular` | `common/buildings/pif_19_cosmic_storm_buildings_building_astrometeorology_observation_center.txt` |
| `building_storm_summoning_theater` | `regular` | `common/buildings/pif_19_cosmic_storm_buildings_building_storm_summoning_theater.txt` |
| `building_storm_holo_theater` | `regular` | `common/buildings/pif_19_cosmic_storm_buildings_building_storm_holo_theater.txt` |
| `building_storm_grand_theater` | `regular` | `common/buildings/pif_19_cosmic_storm_buildings_building_storm_grand_theater.txt` |

### `buildings/20_machine_age_buildings.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `building_augmentation_bazaars` | `regular` | `common/buildings/pif_20_machine_age_buildings_building_augmentation_bazaars.txt` |
| `building_transcendental_retreat` | `regular` | `common/buildings/pif_20_machine_age_buildings_building_transcendental_retreat.txt` |
| `building_hive_transcendental_retreat` | `regular` | `common/buildings/pif_20_machine_age_buildings_building_hive_transcendental_retreat.txt` |
| `building_amphitheater_of_the_mind` | `regular` | `common/buildings/pif_20_machine_age_buildings_building_amphitheater_of_the_mind.txt` |
| `building_grand_concert_hall_of_the_mind` | `regular` | `common/buildings/pif_20_machine_age_buildings_building_grand_concert_hall_of_the_mind.txt` |
| `building_battlement_of_steel` | `regular` | `common/buildings/pif_20_machine_age_buildings_building_battlement_of_steel.txt` |
| `building_grand_battlements_of_steel` | `regular` | `common/buildings/pif_20_machine_age_buildings_building_grand_battlements_of_steel.txt` |
| `building_sanctuary_of_toil` | `regular` | `common/buildings/pif_20_machine_age_buildings_building_sanctuary_of_toil.txt` |
| `building_grand_cathedral_of_toil` | `regular` | `common/buildings/pif_20_machine_age_buildings_building_grand_cathedral_of_toil.txt` |
| `building_forge_of_the_fellowship` | `regular` | `common/buildings/pif_20_machine_age_buildings_building_forge_of_the_fellowship.txt` |
| `building_grand_forge_of_the_fellowship` | `regular` | `common/buildings/pif_20_machine_age_buildings_building_grand_forge_of_the_fellowship.txt` |
| `building_the_sanctum_of_augmentation` | `regular` | `common/buildings/pif_20_machine_age_buildings_building_the_sanctum_of_augmentation.txt` |
| `building_the_united_sanctum_of_augmentation` | `regular` | `common/buildings/pif_20_machine_age_buildings_building_the_united_sanctum_of_augmentation.txt` |
| `building_identity_repository` | `regular` | `common/buildings/pif_20_machine_age_buildings_building_identity_repository.txt` |
| `building_abandoned_gene_clinic` | `regular` | `common/buildings/pif_20_machine_age_buildings_building_abandoned_gene_clinic.txt` |
| `building_lathe_capital` | `capital` | `common/buildings/pif_20_machine_age_buildings_building_lathe_capital.txt` |
| `building_lathe_major_capital` | `capital` | `common/buildings/pif_20_machine_age_buildings_building_lathe_major_capital.txt` |
| `building_lathe_super_capital` | `capital` | `common/buildings/pif_20_machine_age_buildings_building_lathe_super_capital.txt` |
| `building_lathe_resonator` | `regular` | `common/buildings/pif_20_machine_age_buildings_building_lathe_resonator.txt` |
| `building_lathe_stabilisator` | `regular` | `common/buildings/pif_20_machine_age_buildings_building_lathe_stabilisator.txt` |
| `building_lathe_overclocker` | `regular` | `common/buildings/pif_20_machine_age_buildings_building_lathe_overclocker.txt` |
| `building_lathe_preserver` | `regular` | `common/buildings/pif_20_machine_age_buildings_building_lathe_preserver.txt` |
| `building_lathe_reactor` | `regular` | `common/buildings/pif_20_machine_age_buildings_building_lathe_reactor.txt` |
| `building_lathe_life_support` | `regular` | `common/buildings/pif_20_machine_age_buildings_building_lathe_life_support.txt` |
| `building_lathe_cogitator` | `regular` | `common/buildings/pif_20_machine_age_buildings_building_lathe_cogitator.txt` |
| `building_lathe_validator` | `regular` | `common/buildings/pif_20_machine_age_buildings_building_lathe_validator.txt` |
| `building_augmentation_center` | `regular` | `common/buildings/pif_20_machine_age_buildings_building_augmentation_center.txt` |
| `building_cyberdome` | `regular` | `common/buildings/pif_20_machine_age_buildings_building_cyberdome.txt` |
| `building_identity_complex` | `regular` | `common/buildings/pif_20_machine_age_buildings_building_identity_complex.txt` |
| `building_nanolab_1` | `regular` | `common/buildings/pif_20_machine_age_buildings_building_nanolab_1.txt` |
| `building_nanolab_2` | `regular` | `common/buildings/pif_20_machine_age_buildings_building_nanolab_2.txt` |
| `building_nanotech_cauldron` | `regular` | `common/buildings/pif_20_machine_age_buildings_building_nanotech_cauldron.txt` |

### `buildings/21_grand_archive_buildings.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `xeno_geology_holomuseum` | `special` | `common/buildings/pif_21_grand_archive_buildings_xeno_geology_holomuseum.txt` |
| `aesthetic_wonders_holomuseum` | `special` | `common/buildings/pif_21_grand_archive_buildings_aesthetic_wonders_holomuseum.txt` |
| `galactic_history_holomuseum` | `special` | `common/buildings/pif_21_grand_archive_buildings_galactic_history_holomuseum.txt` |
| `wildlife_ranch` | `special` | `common/buildings/pif_21_grand_archive_buildings_wildlife_ranch.txt` |
| `wildlife_ranch_2` | `special` | `common/buildings/pif_21_grand_archive_buildings_wildlife_ranch_2.txt` |
| `wildlife_ranch_3` | `special` | `common/buildings/pif_21_grand_archive_buildings_wildlife_ranch_3.txt` |
| `hunting_grounds` | `special` | `common/buildings/pif_21_grand_archive_buildings_hunting_grounds.txt` |
| `hunting_grounds_2` | `special` | `common/buildings/pif_21_grand_archive_buildings_hunting_grounds_2.txt` |
| `hunting_grounds_3` | `special` | `common/buildings/pif_21_grand_archive_buildings_hunting_grounds_3.txt` |
| `wildlife_sanctuary` | `special` | `common/buildings/pif_21_grand_archive_buildings_wildlife_sanctuary.txt` |
| `wildlife_sanctuary_2` | `special` | `common/buildings/pif_21_grand_archive_buildings_wildlife_sanctuary_2.txt` |
| `wildlife_sanctuary_3` | `special` | `common/buildings/pif_21_grand_archive_buildings_wildlife_sanctuary_3.txt` |
| `primal_arena` | `special` | `common/buildings/pif_21_grand_archive_buildings_primal_arena.txt` |
| `primal_arena_2` | `special` | `common/buildings/pif_21_grand_archive_buildings_primal_arena_2.txt` |
| `primal_arena_3` | `special` | `common/buildings/pif_21_grand_archive_buildings_primal_arena_3.txt` |
| `symbiosis_nexus` | `special` | `common/buildings/pif_21_grand_archive_buildings_symbiosis_nexus.txt` |
| `symbiosis_nexus_2` | `special` | `common/buildings/pif_21_grand_archive_buildings_symbiosis_nexus_2.txt` |
| `symbiosis_nexus_3` | `special` | `common/buildings/pif_21_grand_archive_buildings_symbiosis_nexus_3.txt` |

### `buildings/21_wilderness_buildings.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `building_colony_shelter_wilderness` | `capital` | `common/buildings/pif_21_wilderness_buildings_building_colony_shelter_wilderness.txt` |
| `building_capital_wilderness` | `capital` | `common/buildings/pif_21_wilderness_buildings_building_capital_wilderness.txt` |
| `building_major_capital_wilderness` | `capital` | `common/buildings/pif_21_wilderness_buildings_building_major_capital_wilderness.txt` |
| `building_system_capital_wilderness` | `capital` | `common/buildings/pif_21_wilderness_buildings_building_system_capital_wilderness.txt` |
| `building_imperial_capital_wilderness` | `capital` | `common/buildings/pif_21_wilderness_buildings_building_imperial_capital_wilderness.txt` |
| `building_cradle_of_rebirth` | `regular` | `common/buildings/pif_21_wilderness_buildings_building_cradle_of_rebirth.txt` |
| `building_tendril_cradle_1` | `regular` | `common/buildings/pif_21_wilderness_buildings_building_tendril_cradle_1.txt` |
| `building_tendril_cradle_2` | `regular` | `common/buildings/pif_21_wilderness_buildings_building_tendril_cradle_2.txt` |
| `building_tendril_cradle_3` | `regular` | `common/buildings/pif_21_wilderness_buildings_building_tendril_cradle_3.txt` |
| `building_tendril_cradle_4` | `regular` | `common/buildings/pif_21_wilderness_buildings_building_tendril_cradle_4.txt` |
| `building_brain_node_1` | `regular` | `common/buildings/pif_21_wilderness_buildings_building_brain_node_1.txt` |
| `building_brain_node_2` | `regular` | `common/buildings/pif_21_wilderness_buildings_building_brain_node_2.txt` |
| `building_brain_node_3` | `regular` | `common/buildings/pif_21_wilderness_buildings_building_brain_node_3.txt` |
| `building_brain_node_4` | `regular` | `common/buildings/pif_21_wilderness_buildings_building_brain_node_4.txt` |
| `building_commensal_clearing_1` | `regular` | `common/buildings/pif_21_wilderness_buildings_building_commensal_clearing_1.txt` |
| `building_commensal_clearing_2` | `regular` | `common/buildings/pif_21_wilderness_buildings_building_commensal_clearing_2.txt` |
| `building_commensal_clearing_3` | `regular` | `common/buildings/pif_21_wilderness_buildings_building_commensal_clearing_3.txt` |
| `building_commensal_clearing_4` | `regular` | `common/buildings/pif_21_wilderness_buildings_building_commensal_clearing_4.txt` |
| `building_massive_growth_1` | `regular` | `common/buildings/pif_21_wilderness_buildings_building_massive_growth_1.txt` |
| `building_massive_growth_2` | `regular` | `common/buildings/pif_21_wilderness_buildings_building_massive_growth_2.txt` |
| `building_massive_growth_3` | `regular` | `common/buildings/pif_21_wilderness_buildings_building_massive_growth_3.txt` |
| `building_massive_growth_4` | `regular` | `common/buildings/pif_21_wilderness_buildings_building_massive_growth_4.txt` |
| `building_bioelectric_stimulator_1` | `regular` | `common/buildings/pif_21_wilderness_buildings_building_bioelectric_stimulator_1.txt` |
| `building_bioelectric_stimulator_2` | `regular` | `common/buildings/pif_21_wilderness_buildings_building_bioelectric_stimulator_2.txt` |
| `building_bioelectric_stimulator_3` | `regular` | `common/buildings/pif_21_wilderness_buildings_building_bioelectric_stimulator_3.txt` |
| `building_bioelectric_stimulator_4` | `regular` | `common/buildings/pif_21_wilderness_buildings_building_bioelectric_stimulator_4.txt` |
| `building_churning_tunnels_1` | `regular` | `common/buildings/pif_21_wilderness_buildings_building_churning_tunnels_1.txt` |
| `building_churning_tunnels_2` | `regular` | `common/buildings/pif_21_wilderness_buildings_building_churning_tunnels_2.txt` |
| `building_churning_tunnels_3` | `regular` | `common/buildings/pif_21_wilderness_buildings_building_churning_tunnels_3.txt` |
| `building_churning_tunnels_4` | `regular` | `common/buildings/pif_21_wilderness_buildings_building_churning_tunnels_4.txt` |
| `building_natural_furnace_0` | `regular` | `common/buildings/pif_21_wilderness_buildings_building_natural_furnace_0.txt` |
| `building_natural_furnace_1` | `regular` | `common/buildings/pif_21_wilderness_buildings_building_natural_furnace_1.txt` |
| `building_natural_furnace_2` | `regular` | `common/buildings/pif_21_wilderness_buildings_building_natural_furnace_2.txt` |
| `building_natural_furnace_3` | `regular` | `common/buildings/pif_21_wilderness_buildings_building_natural_furnace_3.txt` |
| `building_avatar_chamber_1` | `regular` | `common/buildings/pif_21_wilderness_buildings_building_avatar_chamber_1.txt` |
| `building_avatar_chamber_2` | `regular` | `common/buildings/pif_21_wilderness_buildings_building_avatar_chamber_2.txt` |
| `building_avatar_chamber_3` | `regular` | `common/buildings/pif_21_wilderness_buildings_building_avatar_chamber_3.txt` |
| `building_avatar_chamber_4` | `regular` | `common/buildings/pif_21_wilderness_buildings_building_avatar_chamber_4.txt` |
| `building_mote_aggravator` | `regular` | `common/buildings/pif_21_wilderness_buildings_building_mote_aggravator.txt` |
| `building_churning_stomach` | `regular` | `common/buildings/pif_21_wilderness_buildings_building_churning_stomach.txt` |
| `building_crystal_growth` | `regular` | `common/buildings/pif_21_wilderness_buildings_building_crystal_growth.txt` |
| `building_planetary_carapace` | `regular` | `common/buildings/pif_21_wilderness_buildings_building_planetary_carapace.txt` |
| `building_planetary_carapace_2` | `regular` | `common/buildings/pif_21_wilderness_buildings_building_planetary_carapace_2.txt` |
| `building_ozone_thickener` | `regular` | `common/buildings/pif_21_wilderness_buildings_building_ozone_thickener.txt` |
| `building_wilderness_storm_relief` | `regular` | `common/buildings/pif_21_wilderness_buildings_building_wilderness_storm_relief.txt` |
| `building_subterranean_cache` | `regular` | `common/buildings/pif_21_wilderness_buildings_building_subterranean_cache.txt` |

### `buildings/22_biogenesis_buildings.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `building_citadel_uplink` | `regular` | `common/buildings/pif_22_biogenesis_buildings_building_citadel_uplink.txt` |
| `building_genomic_facility` | `regular` | `common/buildings/pif_22_biogenesis_buildings_building_genomic_facility.txt` |

### `buildings/22_extreme_frontiers_buildings.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `building_pinniped_sanctuary` | `regular` | `common/buildings/pif_22_extreme_frontiers_buildings_building_pinniped_sanctuary.txt` |
| `building_cryovault` | `regular` | `common/buildings/pif_22_extreme_frontiers_buildings_building_cryovault.txt` |
| `building_bio_furnace` | `regular` | `common/buildings/pif_22_extreme_frontiers_buildings_building_bio_furnace.txt` |

### `buildings/23_shroud_buildings.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `building_lifecrypt_1` | `regular` | `common/buildings/pif_23_shroud_buildings_building_lifecrypt_1.txt` |
| `building_lifecrypt_2` | `regular` | `common/buildings/pif_23_shroud_buildings_building_lifecrypt_2.txt` |
| `building_lifecrypt_3` | `regular` | `common/buildings/pif_23_shroud_buildings_building_lifecrypt_3.txt` |
| `building_lifecrypt_machine_1` | `regular` | `common/buildings/pif_23_shroud_buildings_building_lifecrypt_machine_1.txt` |
| `building_lifecrypt_machine_2` | `regular` | `common/buildings/pif_23_shroud_buildings_building_lifecrypt_machine_2.txt` |
| `building_lifecrypt_machine_3` | `regular` | `common/buildings/pif_23_shroud_buildings_building_lifecrypt_machine_3.txt` |
| `building_lifecrypt_hive_mind_1` | `regular` | `common/buildings/pif_23_shroud_buildings_building_lifecrypt_hive_mind_1.txt` |
| `building_lifecrypt_hive_mind_2` | `regular` | `common/buildings/pif_23_shroud_buildings_building_lifecrypt_hive_mind_2.txt` |
| `building_lifecrypt_hive_mind_3` | `regular` | `common/buildings/pif_23_shroud_buildings_building_lifecrypt_hive_mind_3.txt` |
| `building_lifecrypt_corporate_1` | `regular` | `common/buildings/pif_23_shroud_buildings_building_lifecrypt_corporate_1.txt` |
| `building_lifecrypt_corporate_2` | `regular` | `common/buildings/pif_23_shroud_buildings_building_lifecrypt_corporate_2.txt` |
| `building_lifecrypt_corporate_3` | `regular` | `common/buildings/pif_23_shroud_buildings_building_lifecrypt_corporate_3.txt` |
| `building_experimentation_chambers_1` | `regular` | `common/buildings/pif_23_shroud_buildings_building_experimentation_chambers_1.txt` |
| `building_experimentation_chambers_2` | `regular` | `common/buildings/pif_23_shroud_buildings_building_experimentation_chambers_2.txt` |
| `building_experimentation_chambers_3` | `regular` | `common/buildings/pif_23_shroud_buildings_building_experimentation_chambers_3.txt` |
| `building_cradle_sanctum` | `regular` | `common/buildings/pif_23_shroud_buildings_building_cradle_sanctum.txt` |
| `building_psionic_suppressor` | `regular` | `common/buildings/pif_23_shroud_buildings_building_psionic_suppressor.txt` |
| `building_ancient_ward_1` | `regular` | `common/buildings/pif_23_shroud_buildings_building_ancient_ward_1.txt` |
| `building_ancient_ward_2` | `regular` | `common/buildings/pif_23_shroud_buildings_building_ancient_ward_2.txt` |
| `building_materiality_engine` | `regular` | `common/buildings/pif_23_shroud_buildings_building_materiality_engine.txt` |
| `building_chamber_of_silence` | `regular` | `common/buildings/pif_23_shroud_buildings_building_chamber_of_silence.txt` |

## Source files and documentation used

| Type | Files |
| --- | --- |
| Vanilla object files | `common/buildings/*.txt` |
| Inline scripts | reachable files under `common/inline_scripts/` |
| Scripted variables | `common/scripted_variables/*.txt` |
| Object documentation | `common/buildings/00_example.txt` and actual `common/buildings` objects |
| Generated reports | `Analytics/reports/buildings/` |
