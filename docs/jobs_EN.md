# Jobs — PIF Technical Specification

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

This document describes the technical organization of the `pop_jobs` layer in Planetary Infrastructure Framework. It defines how PIF analyzes jobs, eligibility logic, pop assignment weights, economy, swap data, automation flags, modifier blocks, variables, and validation against vanilla behavior.

## Layer overview

`pop_jobs` describe what work pops can perform, who may fill a job, how strongly a pop prefers the job, which resources the job produces or consumes, which modifier effects it creates, and how the job participates in automation, promotion, demotion, and swap logic.

Jobs differ from buildings because top-level boolean flags often represent independently useful modding logic. PIF therefore extracts those flags into the variable layer, but does not convert every nested `yes/no` inside trigger blocks into variables.

## Analysis methodology

### Parameter analysis

Parameters are analyzed after recursive expansion of reachable `inline_script` calls. PIF uses the actual structure of the object, not comments, assumed file purpose, or variable names. If a parameter is a modifier-carrier block, its category may be determined by the content of the block rather than only by the parameter name.

### Variable analysis

Variable domains are designed separately from parameter categories: they describe what a value controls in gameplay or balance, not where it appears in the AST. For jobs, top-level boolean flags are treated as meaningful variables because they control capped logic, automation, priority UI, AI availability, and similar behavior. Vanilla `@variables` are resolved into concrete values and replaced by PIF-specific variables so that old global conflict points are not preserved. `value:` expressions and control-flow constants are not converted into PIF variables.

### Inline script analysis

All reachable vanilla inline scripts are classified after recursive expansion. `WHOLE` means that the script belongs to a single PIF category. `SPLIT` means that the script mixes several categories and must be distributed into PIF-owned category scripts. If a single modifier block mixes several meanings, it is not split line-by-line and is moved to the fallback category.

## Object classes

Object classes are used to choose the correct PIF schema. They are not used to change gameplay; they describe which structural hooks are safe for this kind of object.

| Class | Objects | Purpose |
| --- | --- | --- |
| ruler | 14 | Jobs with `category = ruler`. |
| specialist | 102 | Jobs with `category = specialist`. |
| worker | 52 | Jobs with `category = worker`. |
| complex_drone | 80 | Gestalt jobs with `category = complex_drone`. |
| simple_drone | 32 | Gestalt jobs with `category = simple_drone`. |
| special/other | 75 | Purge, pre-sapient, precursor, unemployment, criminal, slave, assimilation, and other special categories. |
| no category | 18 | Jobs without a top-level `category`; this is not treated as an error and is preserved as a separate analysis class. |

## PIF layer architecture

### Object files

Each vanilla object is moved into a separate normalized PIF object file:

```txt
common/pop_jobs/pif_<vanilla_file_stem>_<job_key>.txt
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
common/inline_scripts/pif/jobs/<job_key>/<category>.txt
```

A category script is the minimal conflict zone. A mod that changes only the economy of an object should not need to overwrite availability, lifecycle, or AI of the same object.

### Category order

Category script order is fixed and is part of the PIF schema:

```txt
swap
availability
pop_config
economy
planet_state
country_modifiers
pop_modifiers
economic_modifiers
tpm
```

The order is required for reproducible generation, readability, and correct static validation. It must not be changed by incidental sorting.

## Parameter categories

Parameter categories define which PIF-owned inline script owns a particular part of the object. A parameter category does not have to match the variable domain. Modifier-carrier parameters are classified by block content; `triggered_planet_modifier` itself is not treated as a category.

| Category | Location | Purpose | Parameters |
| --- | --- | --- | --- |
| METADATA | Root object | Identity fields that define what the job is. | `category`, `purge`. |
| SWAP | Inline script | Job swap data. | `swappable_data`. |
| AVAILABILITY | Inline script | Eligibility and cap logic for whether a pop may fill the job. | `possible_pre_triggers`, `possible_precalc`, `possible`, `is_capped_by_modifier`. |
| POP_CONFIG | Inline script | Assignment, tags, automation, promotion/demotion, and top-level job flags. | `weight`, `tags`, `promotion`, `demotion`, `auto_trait_prio`, top-level flags. |
| ECONOMY | Inline script | Normal and overlord-directed job economy. | `resources`, `overlord_resources`. |
| PLANET_STATE | Inline script | Clean planet-state modifier blocks. | Amenities, crime, stability, defense armies. |
| COUNTRY_MODIFIERS | Inline script | Clean country-level modifier blocks. | Naval cap, edict fund, leader and country effects. |
| POP_MODIFIERS | Inline script | Clean pop-level modifier blocks. | Happiness, growth, assembly, workforce, pop-group modifiers. |
| ECONOMIC_MODIFIERS | Inline script | Clean output/upkeep modifier blocks outside `resources`. | Job output and upkeep modifier keys. |
| TPM | Inline script | Fallback for mixed, system, rare, and special modifier blocks. | Mixed modifier carriers and rare effects. |

## Variable categories

| Domain file | Variables | Purpose |
| --- | --- | --- |
| `pif_jobs_country_modifiers_variables.txt` | 116 | Country-level values from job modifiers. |
| `pif_jobs_demotion_variables.txt` | 36 | Demotion time values. |
| `pif_jobs_economic_modifiers_variables.txt` | 55 | Economic modifier values outside regular job resources. |
| `pif_jobs_flags_variables.txt` | 320 | Top-level boolean job flags. |
| `pif_jobs_output_variables.txt` | 532 | Normal job output for the planet owner. |
| `pif_jobs_overlord_output_variables.txt` | 96 | Output delivered to the overlord side. |
| `pif_jobs_planet_state_variables.txt` | 256 | Planet-state values from job modifiers. |
| `pif_jobs_pop_modifiers_variables.txt` | 59 | Pop-level values from job modifiers. |
| `pif_jobs_promotion_variables.txt` | 208 | Promotion time values. |
| `pif_jobs_tpm_variables.txt` | 51 | Fallback values from mixed or rare job modifier blocks. |
| `pif_jobs_upkeep_variables.txt` | 301 | Normal job upkeep paid by the planet owner. |
| `pif_jobs_weight_variables.txt` | 652 | Pop assignment weights for jobs. |

Total: **12** variable files and **2682** variables.

## Inline Scripts

### Inline script policy

Vanilla inline scripts are used as source material for PIF-owned category scripts. `WHOLE` means that the expanded script belongs to one category. `SPLIT` means that the expanded script must be distributed across categories. This layer has **27** reachable inline scripts: **17** `WHOLE`, **10** `SPLIT`.

### Reachable inline scripts

| Inline script | Decision | Categories | Parameters |
| --- | --- | --- | --- |
| `jobs/academia_recruiter_naval_cap_add` | `WHOLE` | `country_modifiers` | `triggered_country_modifier` |
| `jobs/automodding_priority_alloys` | `WHOLE` | `pop_config` | `auto_trait_prio` |
| `jobs/automodding_priority_charisma` | `WHOLE` | `pop_config` | `auto_trait_prio` |
| `jobs/automodding_priority_consumer_goods` | `WHOLE` | `pop_config` | `auto_trait_prio` |
| `jobs/automodding_priority_energy` | `WHOLE` | `pop_config` | `auto_trait_prio` |
| `jobs/automodding_priority_food` | `WHOLE` | `pop_config` | `auto_trait_prio` |
| `jobs/automodding_priority_minerals` | `WHOLE` | `pop_config` | `auto_trait_prio` |
| `jobs/automodding_priority_research` | `WHOLE` | `pop_config` | `auto_trait_prio` |
| `jobs/automodding_priority_trade` | `WHOLE` | `pop_config` | `auto_trait_prio` |
| `jobs/automodding_priority_unity` | `WHOLE` | `pop_config` | `auto_trait_prio` |
| `jobs/ethic_job_modifiers` | `SPLIT` | `country_modifiers economic_modifiers planet_state pop_modifiers` | `triggered_country_modifier triggered_planet_modifier` |
| `jobs/ethic_job_modifiers_memorialist` | `SPLIT` | `country_modifiers economic_modifiers planet_state pop_modifiers` | `triggered_country_modifier triggered_planet_modifier` |
| `jobs/ethic_job_resources` | `WHOLE` | `metadata` | `produces` |
| `jobs/ethic_job_resources_memorialist` | `WHOLE` | `metadata` | `produces` |
| `jobs/inf_navalcap_jobs` | `WHOLE` | `country_modifiers` | `triggered_country_modifier` |
| `jobs/job_enforcer` | `SPLIT` | `economic_modifiers economy planet_state pop_modifiers tpm` | `resources triggered_planet_modifier` |
| `jobs/job_enforcer_additional_modifiers` | `SPLIT` | `economic_modifiers planet_state pop_modifiers` | `triggered_planet_modifier` |
| `jobs/job_enforcer_triggered_resources` | `WHOLE` | `metadata` | `produces upkeep` |
| `jobs/job_telepath` | `SPLIT` | `availability country_modifiers economic_modifiers economy planet_state pop_config pop_modifiers tpm` | `auto_trait_prio possible possible_pre_triggers resources tags triggered_country_modifier triggered_planet_modifier` |
| `jobs/job_telepath_additional_modifiers` | `SPLIT` | `country_modifiers economic_modifiers planet_state pop_modifiers tpm` | `triggered_country_modifier triggered_planet_modifier` |
| `output/factory_output` | `WHOLE` | `nan` | `nan` |
| `output/foundry_output` | `WHOLE` | `metadata` | `produces upkeep` |
| `output/genomic_triggered_modifiers` | `SPLIT` | `country_modifiers planet_state` | `triggered_country_modifier triggered_planet_modifier` |
| `output/healthcare_triggered_modifiers` | `SPLIT` | `economic_modifiers planet_state pop_modifiers` | `triggered_planet_modifier` |
| `output/researcher_output` | `WHOLE` | `nan` | `nan` |
| `output/soldier_triggered_modifiers` | `SPLIT` | `country_modifiers planet_state` | `planet_modifier triggered_country_modifier triggered_planet_modifier` |
| `shroud/jobs/colonist_job` | `SPLIT` | `availability economy metadata planet_state pop_config swap tpm` | `category exempt_from_ai_amenity_prioritization planet_modifier possible_pre_triggers possible_precalc promotion resources swappable_data tags triggered_planet_modifier weight` |

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

Important areas include `weight`, `promotion`, `demotion`, repeated modifier blocks, `auto_trait_prio`, and category inline call order.

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

Current result: **373 / 373 OK**, failed: **0**.

## Runtime validation

Static validation confirms structural equivalence, but runtime smoke testing is still required because the engine may depend on context that is not visible in AST comparison.

A minimal runtime check should include starting a new game, opening the planetary UI, checking regular empire, hive, machine, and corporate contexts, habitats/ringworld/ecumenopolis when possible, and reviewing `error.log` for errors related to `pif_` files.

## Layer statistics

| Metric | Value |
| --- | --- |
| Objects | 373 |
| Source files | 21 |
| Parameter names after expansion | 31 |
| Category inline scripts | 3357 |
| Variable files | 12 |
| PIF variables | 2682 |
| Reachable inline scripts | 27 |
| Inline scripts WHOLE | 17 |
| Inline scripts SPLIT | 10 |
| Validation checked | 373 |
| Validation OK | 373 |
| Validation failed | 0 |

## Parameter statistics

| Parameter | Type | Total | Ruler | Specialist | Worker | Complex drone | Simple drone | Special/other | No category | Purpose | Category | Action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `is_capped_by_modifier` | modifier / flag | 173 | 3 | 32 | 30 | 20 | 18 | 70 | 0 | Marks that the number of jobs is controlled by `job_<key>_add` modifiers. | AVAILABILITY | Move into the corresponding PIF-owned category inline script. |
| `possible` | trigger block | 328 | 13 | 79 | 42 | 72 | 30 | 74 | 18 | Main condition for whether a pop can fill the job. | AVAILABILITY | Move into the corresponding PIF-owned category inline script. |
| `possible_pre_triggers` | trigger block | 302 | 8 | 84 | 45 | 62 | 29 | 74 | 0 | Fast pre-filters before `possible`. | AVAILABILITY | Move into the corresponding PIF-owned category inline script. |
| `possible_precalc` | atom / enum | 216 | 7 | 69 | 30 | 62 | 27 | 21 | 0 | Precalculated eligibility filter for the job. | AVAILABILITY | Move into the corresponding PIF-owned category inline script. |
| `overlord_resources` | resources block | 61 | 0 | 19 | 13 | 17 | 9 | 3 | 0 | Job economic block directed to the overlord side in subject/overlord context. | ECONOMY | Move into the corresponding PIF-owned category inline script. |
| `resources` | resources block | 267 | 8 | 78 | 39 | 61 | 24 | 57 | 0 | Economic block: cost, upkeep, produces, and economic category. | ECONOMY | Move into the corresponding PIF-owned category inline script. |
| `category` | atom / enum | 355 | 14 | 102 | 52 | 80 | 32 | 75 | 0 | Vanilla object category. | METADATA | Keep in the root object. |
| `purge` | atom / enum | 4 | 0 | 0 | 0 | 0 | 0 | 4 | 0 | Purge logic type for a job. | METADATA | Keep in the root object. |
| `allow_only_same_rank_pops` | yes/no | 6 | 0 | 0 | 0 | 0 | 0 | 6 | 0 | Allows only pops of the same rank or stratum. | POP_CONFIG | Move into the corresponding PIF-owned category inline script. |
| `auto_generate_description` | yes/no | 2 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | Controls automatic effect description generation. | POP_CONFIG | Move into the corresponding PIF-owned category inline script. |
| `auto_trait_prio` | block / value | 126 | 4 | 47 | 21 | 34 | 15 | 5 | 0 | Auto-modding trait priorities for the job. | POP_CONFIG | Move into the corresponding PIF-owned category inline script. |
| `can_be_automated` | yes/no | 10 | 1 | 4 | 1 | 2 | 0 | 2 | 0 | Whether the job participates in automation. | POP_CONFIG | Move into the corresponding PIF-owned category inline script. |
| `can_set_priority` | yes/no | 51 | 0 | 13 | 7 | 13 | 6 | 12 | 0 | Whether the job priority can be changed manually. | POP_CONFIG | Move into the corresponding PIF-owned category inline script. |
| `contributes_to_diplo_weight` | yes/no | 24 | 0 | 0 | 0 | 0 | 0 | 24 | 0 | Whether the job contributes to diplomatic weight calculations. | POP_CONFIG | Move into the corresponding PIF-owned category inline script. |
| `count_as_available_for_ai` | yes/no | 11 | 0 | 0 | 1 | 0 | 0 | 10 | 0 | Whether the job counts as available for AI. | POP_CONFIG | Move into the corresponding PIF-owned category inline script. |
| `demotion` | block / value | 36 | 0 | 0 | 0 | 0 | 0 | 36 | 0 | Demotion rules out of the job or stratum. | POP_CONFIG | Move into the corresponding PIF-owned category inline script. |
| `exempt_from_ai_amenity_prioritization` | yes/no | 3 | 0 | 2 | 1 | 0 | 0 | 0 | 0 | Exemption from AI amenity prioritization. | POP_CONFIG | Move into the corresponding PIF-owned category inline script. |
| `first_come_first_served` | yes/no | 27 | 0 | 0 | 2 | 0 | 0 | 25 | 0 | First come first served job filling behavior. | POP_CONFIG | Move into the corresponding PIF-owned category inline script. |
| `ignores_sapience` | yes/no | 13 | 0 | 0 | 0 | 0 | 0 | 13 | 0 | Whether the job ignores pop sapience. | POP_CONFIG | Move into the corresponding PIF-owned category inline script. |
| `promotion` | block / value | 208 | 8 | 78 | 35 | 56 | 27 | 4 | 0 | Promotion rules into the job or stratum. | POP_CONFIG | Move into the corresponding PIF-owned category inline script. |
| `tags` | list / block | 251 | 8 | 75 | 41 | 55 | 26 | 46 | 0 | Job tags used by AI, automation, scripted checks, and grouping. | POP_CONFIG | Move into the corresponding PIF-owned category inline script. |
| `triggered_tags` | block / value | 2 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | Conditional job tags. | POP_CONFIG | Move into the corresponding PIF-owned category inline script. |
| `weight` | block / value | 290 | 7 | 81 | 45 | 59 | 29 | 69 | 0 | Weight used to assign pops to the job. | POP_CONFIG | Move into the corresponding PIF-owned category inline script. |
| `swappable_data` | block / value | 352 | 14 | 102 | 49 | 80 | 32 | 59 | 16 | Data used by job swap logic. | SWAP | Move into the corresponding PIF-owned category inline script. |
| `country_modifier` | modifier / flag | 12 | 1 | 7 | 0 | 4 | 0 | 0 | 0 | Static country modifier carrier. | content-based modifier category | Classify the block by content; normalize static modifier carriers when required. |
| `planet_modifier` | modifier / flag | 52 | 1 | 17 | 9 | 12 | 3 | 10 | 0 | Static planet modifier carrier. | content-based modifier category | Classify the block by content; normalize static modifier carriers when required. |
| `system_modifier` | modifier / flag | 2 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | System-level modifier carrier. | content-based modifier category | Classify the block by content; normalize static modifier carriers when required. |
| `triggered_country_modifier` | modifier / flag | 48 | 1 | 23 | 4 | 17 | 2 | 1 | 0 | Triggered country modifier carrier. | content-based modifier category | Classify the block by content; normalize static modifier carriers when required. |
| `triggered_planet_modifier` | modifier / flag | 123 | 8 | 38 | 18 | 20 | 9 | 30 | 0 | Triggered planet modifier carrier. | content-based modifier category | Classify the block by content; normalize static modifier carriers when required. |
| `triggered_planet_pop_group_modifier_for_all` | modifier / flag | 2 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | Triggered modifier for all planet pop groups. | content-based modifier category | Classify the block by content; normalize static modifier carriers when required. |
| `triggered_planet_pop_group_modifier_for_species` | modifier / flag | 6 | 0 | 2 | 0 | 4 | 0 | 0 | 0 | Triggered modifier for species-specific pop groups. | content-based modifier category | Classify the block by content; normalize static modifier carriers when required. |

## Special cases and technical warnings

- Jobs without `category` are preserved as a separate analysis class.
- `possible_precalc` must not be inferred from `category`; it is copied from vanilla as-is.
- `auto_trait_prio` belongs to auto-modding species trait selection, not job assignment weight.
- `overlord_resources` is an economy block directed to the overlord side.
- Top-level boolean flags are variables; nested trigger booleans remain literal.

## Affected vanilla objects

This section lists the vanilla objects overridden by PIF for this layer.

### `pop_jobs/00_other_jobs.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `civilian` | `special_other` | `common/pop_jobs/pif_00_other_jobs_civilian.txt` |
| `slave_processing` | `special_other` | `common/pop_jobs/pif_00_other_jobs_slave_processing.txt` |
| `heart_processing` | `special_other` | `common/pop_jobs/pif_00_other_jobs_heart_processing.txt` |
| `slave_unprocessing` | `special_other` | `common/pop_jobs/pif_00_other_jobs_slave_unprocessing.txt` |
| `presapient_unprocessing` | `special_other` | `common/pop_jobs/pif_00_other_jobs_presapient_unprocessing.txt` |
| `servant` | `worker` | `common/pop_jobs/pif_00_other_jobs_servant.txt` |
| `slave_overseer` | `worker` | `common/pop_jobs/pif_00_other_jobs_slave_overseer.txt` |
| `slave_toiler` | `worker` | `common/pop_jobs/pif_00_other_jobs_slave_toiler.txt` |
| `organic_battery` | `worker` | `common/pop_jobs/pif_00_other_jobs_organic_battery.txt` |
| `livestock` | `worker` | `common/pop_jobs/pif_00_other_jobs_livestock.txt` |
| `livestock_infernal` | `worker` | `common/pop_jobs/pif_00_other_jobs_livestock_infernal.txt` |
| `livestock_zoo_animal` | `special_other` | `common/pop_jobs/pif_00_other_jobs_livestock_zoo_animal.txt` |
| `livestock_zoo_beast` | `special_other` | `common/pop_jobs/pif_00_other_jobs_livestock_zoo_beast.txt` |
| `bio_trophy` | `special_other` | `common/pop_jobs/pif_00_other_jobs_bio_trophy.txt` |
| `bio_trophy_processing` | `special_other` | `common/pop_jobs/pif_00_other_jobs_bio_trophy_processing.txt` |
| `bio_trophy_unprocessing` | `special_other` | `common/pop_jobs/pif_00_other_jobs_bio_trophy_unprocessing.txt` |
| `purge` | `special_other` | `common/pop_jobs/pif_00_other_jobs_purge.txt` |
| `purge_unprocessing` | `special_other` | `common/pop_jobs/pif_00_other_jobs_purge_unprocessing.txt` |
| `crisis_purge` | `special_other` | `common/pop_jobs/pif_00_other_jobs_crisis_purge.txt` |
| `assimilation` | `special_other` | `common/pop_jobs/pif_00_other_jobs_assimilation.txt` |
| `criminal` | `special_other` | `common/pop_jobs/pif_00_other_jobs_criminal.txt` |
| `deviant_drone` | `special_other` | `common/pop_jobs/pif_00_other_jobs_deviant_drone.txt` |
| `corrupt_drone` | `special_other` | `common/pop_jobs/pif_00_other_jobs_corrupt_drone.txt` |
| `fotd_protectors` | `worker` | `common/pop_jobs/pif_00_other_jobs_fotd_protectors.txt` |
| `organic_exhibit` | `special_other` | `common/pop_jobs/pif_00_other_jobs_organic_exhibit.txt` |
| `livestock_lithoid` | `worker` | `common/pop_jobs/pif_00_other_jobs_livestock_lithoid.txt` |
| `livestock_zoo_animal_lithoid` | `special_other` | `common/pop_jobs/pif_00_other_jobs_livestock_zoo_animal_lithoid.txt` |
| `livestock_zoo_beast_lithoid` | `special_other` | `common/pop_jobs/pif_00_other_jobs_livestock_zoo_beast_lithoid.txt` |
| `purge_lithoid` | `special_other` | `common/pop_jobs/pif_00_other_jobs_purge_lithoid.txt` |
| `purge_robot` | `special_other` | `common/pop_jobs/pif_00_other_jobs_purge_robot.txt` |
| `purge_processing` | `special_other` | `common/pop_jobs/pif_00_other_jobs_purge_processing.txt` |
| `purge_processing_lithoid` | `special_other` | `common/pop_jobs/pif_00_other_jobs_purge_processing_lithoid.txt` |
| `purge_processing_infernal` | `special_other` | `common/pop_jobs/pif_00_other_jobs_purge_processing_infernal.txt` |
| `purge_processing_robot` | `special_other` | `common/pop_jobs/pif_00_other_jobs_purge_processing_robot.txt` |
| `purge_labor_camps` | `special_other` | `common/pop_jobs/pif_00_other_jobs_purge_labor_camps.txt` |
| `purge_matrix` | `special_other` | `common/pop_jobs/pif_00_other_jobs_purge_matrix.txt` |
| `purge_sacrifice` | `special_other` | `common/pop_jobs/pif_00_other_jobs_purge_sacrifice.txt` |
| `presapient_processing` | `special_other` | `common/pop_jobs/pif_00_other_jobs_presapient_processing.txt` |
| `robot_servant_processing` | `special_other` | `common/pop_jobs/pif_00_other_jobs_robot_servant_processing.txt` |
| `robot_servant_unprocessing` | `special_other` | `common/pop_jobs/pif_00_other_jobs_robot_servant_unprocessing.txt` |

### `pop_jobs/01_ruler_jobs.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `politician` | `ruler` | `common/pop_jobs/pif_01_ruler_jobs_politician.txt` |
| `knight_commander` | `ruler` | `common/pop_jobs/pif_01_ruler_jobs_knight_commander.txt` |
| `dystopian_enforcer` | `ruler` | `common/pop_jobs/pif_01_ruler_jobs_dystopian_enforcer.txt` |
| `dystopian_telepath` | `ruler` | `common/pop_jobs/pif_01_ruler_jobs_dystopian_telepath.txt` |
| `head_researcher` | `ruler` | `common/pop_jobs/pif_01_ruler_jobs_head_researcher.txt` |
| `high_priest` | `ruler` | `common/pop_jobs/pif_01_ruler_jobs_high_priest.txt` |
| `noble` | `ruler` | `common/pop_jobs/pif_01_ruler_jobs_noble.txt` |
| `merchant` | `ruler` | `common/pop_jobs/pif_01_ruler_jobs_merchant.txt` |
| `executive` | `ruler` | `common/pop_jobs/pif_01_ruler_jobs_executive.txt` |
| `warden` | `ruler` | `common/pop_jobs/pif_01_ruler_jobs_warden.txt` |

### `pop_jobs/02_specialist_jobs.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `physicist` | `specialist` | `common/pop_jobs/pif_02_specialist_jobs_physicist.txt` |
| `biologist` | `specialist` | `common/pop_jobs/pif_02_specialist_jobs_biologist.txt` |
| `engineer` | `specialist` | `common/pop_jobs/pif_02_specialist_jobs_engineer.txt` |
| `xeno_zoo_keeper` | `specialist` | `common/pop_jobs/pif_02_specialist_jobs_xeno_zoo_keeper.txt` |
| `bureaucrat` | `specialist` | `common/pop_jobs/pif_02_specialist_jobs_bureaucrat.txt` |
| `enforcer` | `specialist` | `common/pop_jobs/pif_02_specialist_jobs_enforcer.txt` |
| `educator` | `specialist` | `common/pop_jobs/pif_02_specialist_jobs_educator.txt` |
| `telepath` | `specialist` | `common/pop_jobs/pif_02_specialist_jobs_telepath.txt` |
| `entertainer` | `specialist` | `common/pop_jobs/pif_02_specialist_jobs_entertainer.txt` |
| `culture_worker` | `specialist` | `common/pop_jobs/pif_02_specialist_jobs_culture_worker.txt` |
| `unifier` | `specialist` | `common/pop_jobs/pif_02_specialist_jobs_unifier.txt` |
| `chemist` | `specialist` | `common/pop_jobs/pif_02_specialist_jobs_chemist.txt` |
| `translucer` | `specialist` | `common/pop_jobs/pif_02_specialist_jobs_translucer.txt` |
| `gas_refiner` | `specialist` | `common/pop_jobs/pif_02_specialist_jobs_gas_refiner.txt` |
| `roboticist` | `specialist` | `common/pop_jobs/pif_02_specialist_jobs_roboticist.txt` |
| `healthcare` | `specialist` | `common/pop_jobs/pif_02_specialist_jobs_healthcare.txt` |
| `trader` | `specialist` | `common/pop_jobs/pif_02_specialist_jobs_trader.txt` |
| `numistic_priest` | `specialist` | `common/pop_jobs/pif_02_specialist_jobs_numistic_priest.txt` |
| `preacher` | `specialist` | `common/pop_jobs/pif_02_specialist_jobs_preacher.txt` |
| `manager` | `specialist` | `common/pop_jobs/pif_02_specialist_jobs_manager.txt` |
| `steward` | `specialist` | `common/pop_jobs/pif_02_specialist_jobs_steward.txt` |
| `necromancer` | `specialist` | `common/pop_jobs/pif_02_specialist_jobs_necromancer.txt` |
| `death_chronicler` | `specialist` | `common/pop_jobs/pif_02_specialist_jobs_death_chronicler.txt` |
| `necro_apprentice` | `specialist` | `common/pop_jobs/pif_02_specialist_jobs_necro_apprentice.txt` |
| `foundry` | `specialist` | `common/pop_jobs/pif_02_specialist_jobs_foundry.txt` |
| `catalytic_technician` | `specialist` | `common/pop_jobs/pif_02_specialist_jobs_catalytic_technician.txt` |
| `artisan` | `specialist` | `common/pop_jobs/pif_02_specialist_jobs_artisan.txt` |
| `artificer` | `specialist` | `common/pop_jobs/pif_02_specialist_jobs_artificer.txt` |
| `pearl_diver` | `no_category` | `common/pop_jobs/pif_02_specialist_jobs_pearl_diver.txt` |
| `reassigner` | `specialist` | `common/pop_jobs/pif_02_specialist_jobs_reassigner.txt` |
| `bath_attendant` | `specialist` | `common/pop_jobs/pif_02_specialist_jobs_bath_attendant.txt` |
| `bath_attendant_individual_machine` | `specialist` | `common/pop_jobs/pif_02_specialist_jobs_bath_attendant_individual_machine.txt` |
| `knight` | `specialist` | `common/pop_jobs/pif_02_specialist_jobs_knight.txt` |
| `archaeoengineers` | `specialist` | `common/pop_jobs/pif_02_specialist_jobs_archaeoengineers.txt` |
| `resort_worker` | `specialist` | `common/pop_jobs/pif_02_specialist_jobs_resort_worker.txt` |
| `polytechnic_mentor` | `specialist` | `common/pop_jobs/pif_02_specialist_jobs_polytechnic_mentor.txt` |
| `offworld_prospector` | `specialist` | `common/pop_jobs/pif_02_specialist_jobs_offworld_prospector.txt` |
| `soldier` | `specialist` | `common/pop_jobs/pif_02_specialist_jobs_soldier.txt` |
| `battle_thrall` | `specialist` | `common/pop_jobs/pif_02_specialist_jobs_battle_thrall.txt` |

### `pop_jobs/03_worker_jobs.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `colonist` | `worker` | `common/pop_jobs/pif_03_worker_jobs_colonist.txt` |
| `clerk` | `worker` | `common/pop_jobs/pif_03_worker_jobs_clerk.txt` |
| `technician` | `worker` | `common/pop_jobs/pif_03_worker_jobs_technician.txt` |
| `miner` | `worker` | `common/pop_jobs/pif_03_worker_jobs_miner.txt` |
| `crystal_miner` | `worker` | `common/pop_jobs/pif_03_worker_jobs_crystal_miner.txt` |
| `gas_extractor` | `worker` | `common/pop_jobs/pif_03_worker_jobs_gas_extractor.txt` |
| `mote_harvester` | `worker` | `common/pop_jobs/pif_03_worker_jobs_mote_harvester.txt` |
| `farmer` | `worker` | `common/pop_jobs/pif_03_worker_jobs_farmer.txt` |
| `mortal_initiate` | `worker` | `common/pop_jobs/pif_03_worker_jobs_mortal_initiate.txt` |
| `scrap_miner` | `no_category` | `common/pop_jobs/pif_03_worker_jobs_scrap_miner.txt` |
| `angler` | `worker` | `common/pop_jobs/pif_03_worker_jobs_angler.txt` |
| `ranger` | `worker` | `common/pop_jobs/pif_03_worker_jobs_ranger.txt` |
| `squire` | `worker` | `common/pop_jobs/pif_03_worker_jobs_squire.txt` |
| `foundry_prison_worker` | `worker` | `common/pop_jobs/pif_03_worker_jobs_foundry_prison_worker.txt` |
| `catalytic_technician_prison_worker` | `worker` | `common/pop_jobs/pif_03_worker_jobs_catalytic_technician_prison_worker.txt` |
| `artisan_prison_worker` | `worker` | `common/pop_jobs/pif_03_worker_jobs_artisan_prison_worker.txt` |
| `artificer_prison_worker` | `worker` | `common/pop_jobs/pif_03_worker_jobs_artificer_prison_worker.txt` |

### `pop_jobs/04_gestalt_jobs.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `spawning_drone` | `complex_drone` | `common/pop_jobs/pif_04_gestalt_jobs_spawning_drone.txt` |
| `offspring_drone` | `complex_drone` | `common/pop_jobs/pif_04_gestalt_jobs_offspring_drone.txt` |
| `replicator` | `complex_drone` | `common/pop_jobs/pif_04_gestalt_jobs_replicator.txt` |
| `gestation_drone` | `complex_drone` | `common/pop_jobs/pif_04_gestalt_jobs_gestation_drone.txt` |
| `evaluator` | `complex_drone` | `common/pop_jobs/pif_04_gestalt_jobs_evaluator.txt` |
| `coordinator` | `complex_drone` | `common/pop_jobs/pif_04_gestalt_jobs_coordinator.txt` |
| `synapse_drone` | `complex_drone` | `common/pop_jobs/pif_04_gestalt_jobs_synapse_drone.txt` |
| `chronicle_drone` | `complex_drone` | `common/pop_jobs/pif_04_gestalt_jobs_chronicle_drone.txt` |
| `calculator_physicist` | `complex_drone` | `common/pop_jobs/pif_04_gestalt_jobs_calculator_physicist.txt` |
| `brain_drone_physicist` | `complex_drone` | `common/pop_jobs/pif_04_gestalt_jobs_brain_drone_physicist.txt` |
| `calculator_biologist` | `complex_drone` | `common/pop_jobs/pif_04_gestalt_jobs_calculator_biologist.txt` |
| `brain_drone_biologist` | `complex_drone` | `common/pop_jobs/pif_04_gestalt_jobs_brain_drone_biologist.txt` |
| `archaeo_drone` | `complex_drone` | `common/pop_jobs/pif_04_gestalt_jobs_archaeo_drone.txt` |
| `archaeo_unit` | `complex_drone` | `common/pop_jobs/pif_04_gestalt_jobs_archaeo_unit.txt` |
| `calculator_engineer` | `complex_drone` | `common/pop_jobs/pif_04_gestalt_jobs_calculator_engineer.txt` |
| `brain_drone_engineer` | `complex_drone` | `common/pop_jobs/pif_04_gestalt_jobs_brain_drone_engineer.txt` |
| `artisan_drone` | `complex_drone` | `common/pop_jobs/pif_04_gestalt_jobs_artisan_drone.txt` |
| `fabricator` | `complex_drone` | `common/pop_jobs/pif_04_gestalt_jobs_fabricator.txt` |
| `alloy_drone` | `complex_drone` | `common/pop_jobs/pif_04_gestalt_jobs_alloy_drone.txt` |
| `catalytic_drone` | `complex_drone` | `common/pop_jobs/pif_04_gestalt_jobs_catalytic_drone.txt` |
| `chemist_drone` | `complex_drone` | `common/pop_jobs/pif_04_gestalt_jobs_chemist_drone.txt` |
| `translucer_drone` | `complex_drone` | `common/pop_jobs/pif_04_gestalt_jobs_translucer_drone.txt` |
| `gas_refiner_drone` | `complex_drone` | `common/pop_jobs/pif_04_gestalt_jobs_gas_refiner_drone.txt` |
| `patrol_drone` | `complex_drone` | `common/pop_jobs/pif_04_gestalt_jobs_patrol_drone.txt` |
| `mote_harvesting_drone` | `complex_drone` | `common/pop_jobs/pif_04_gestalt_jobs_mote_harvesting_drone.txt` |
| `crystal_mining_drone` | `complex_drone` | `common/pop_jobs/pif_04_gestalt_jobs_crystal_mining_drone.txt` |
| `gas_extraction_drone` | `complex_drone` | `common/pop_jobs/pif_04_gestalt_jobs_gas_extraction_drone.txt` |
| `logistics_drone` | `complex_drone` | `common/pop_jobs/pif_04_gestalt_jobs_logistics_drone.txt` |
| `mining_drone` | `simple_drone` | `common/pop_jobs/pif_04_gestalt_jobs_mining_drone.txt` |
| `scrap_miner_drone` | `simple_drone` | `common/pop_jobs/pif_04_gestalt_jobs_scrap_miner_drone.txt` |
| `agri_drone` | `simple_drone` | `common/pop_jobs/pif_04_gestalt_jobs_agri_drone.txt` |
| `technician_drone` | `simple_drone` | `common/pop_jobs/pif_04_gestalt_jobs_technician_drone.txt` |
| `maintenance_drone` | `special_other` | `common/pop_jobs/pif_04_gestalt_jobs_maintenance_drone.txt` |
| `wilderness_maintenance_drone` | `special_other` | `common/pop_jobs/pif_04_gestalt_jobs_wilderness_maintenance_drone.txt` |
| `warrior_drone` | `complex_drone` | `common/pop_jobs/pif_04_gestalt_jobs_warrior_drone.txt` |
| `bath_attendant_machine` | `simple_drone` | `common/pop_jobs/pif_04_gestalt_jobs_bath_attendant_machine.txt` |
| `bath_attendant_hive` | `simple_drone` | `common/pop_jobs/pif_04_gestalt_jobs_bath_attendant_hive.txt` |
| `polytechnic_drone` | `complex_drone` | `common/pop_jobs/pif_04_gestalt_jobs_polytechnic_drone.txt` |
| `offworld_prospector_drone` | `complex_drone` | `common/pop_jobs/pif_04_gestalt_jobs_offworld_prospector_drone.txt` |

### `pop_jobs/05_primitive_jobs.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `pre_sapient` | `special_other` | `common/pop_jobs/pif_05_primitive_jobs_pre_sapient.txt` |
| `pre_sapient_nascent` | `special_other` | `common/pop_jobs/pif_05_primitive_jobs_pre_sapient_nascent.txt` |
| `hunted_pre_sapient` | `special_other` | `common/pop_jobs/pif_05_primitive_jobs_hunted_pre_sapient.txt` |
| `hunted_pre_sapient_lithoid` | `special_other` | `common/pop_jobs/pif_05_primitive_jobs_hunted_pre_sapient_lithoid.txt` |
| `xeno_zoo_animal` | `special_other` | `common/pop_jobs/pif_05_primitive_jobs_xeno_zoo_animal.txt` |
| `xeno_zoo_animal_nascent` | `special_other` | `common/pop_jobs/pif_05_primitive_jobs_xeno_zoo_animal_nascent.txt` |
| `xeno_zoo_animal_lithoid` | `special_other` | `common/pop_jobs/pif_05_primitive_jobs_xeno_zoo_animal_lithoid.txt` |
| `xeno_zoo_animal_lithoid_nascent` | `special_other` | `common/pop_jobs/pif_05_primitive_jobs_xeno_zoo_animal_lithoid_nascent.txt` |
| `xeno_zoo_beast` | `special_other` | `common/pop_jobs/pif_05_primitive_jobs_xeno_zoo_beast.txt` |
| `xeno_zoo_beast_nascent` | `special_other` | `common/pop_jobs/pif_05_primitive_jobs_xeno_zoo_beast_nascent.txt` |
| `xeno_zoo_beast_lithoid` | `special_other` | `common/pop_jobs/pif_05_primitive_jobs_xeno_zoo_beast_lithoid.txt` |
| `xeno_zoo_beast_lithoid_nascent` | `special_other` | `common/pop_jobs/pif_05_primitive_jobs_xeno_zoo_beast_lithoid_nascent.txt` |
| `hunter_gatherer` | `worker` | `common/pop_jobs/pif_05_primitive_jobs_hunter_gatherer.txt` |
| `hunter_gatherer_lithoid` | `worker` | `common/pop_jobs/pif_05_primitive_jobs_hunter_gatherer_lithoid.txt` |
| `peasant` | `worker` | `common/pop_jobs/pif_05_primitive_jobs_peasant.txt` |
| `peasant_lithoid` | `worker` | `common/pop_jobs/pif_05_primitive_jobs_peasant_lithoid.txt` |
| `primitive_warrior` | `specialist` | `common/pop_jobs/pif_05_primitive_jobs_primitive_warrior.txt` |
| `primitive_noble` | `ruler` | `common/pop_jobs/pif_05_primitive_jobs_primitive_noble.txt` |
| `primitive_researcher` | `specialist` | `common/pop_jobs/pif_05_primitive_jobs_primitive_researcher.txt` |
| `primitive_priest` | `specialist` | `common/pop_jobs/pif_05_primitive_jobs_primitive_priest.txt` |
| `primitive_laborer` | `specialist` | `common/pop_jobs/pif_05_primitive_jobs_primitive_laborer.txt` |
| `primitive_miner` | `worker` | `common/pop_jobs/pif_05_primitive_jobs_primitive_miner.txt` |
| `primitive_technician` | `worker` | `common/pop_jobs/pif_05_primitive_jobs_primitive_technician.txt` |
| `primitive_farmer` | `worker` | `common/pop_jobs/pif_05_primitive_jobs_primitive_farmer.txt` |
| `primitive_researcher_2` | `specialist` | `common/pop_jobs/pif_05_primitive_jobs_primitive_researcher_2.txt` |
| `primitive_priest_2` | `specialist` | `common/pop_jobs/pif_05_primitive_jobs_primitive_priest_2.txt` |
| `primitive_entertainer` | `specialist` | `common/pop_jobs/pif_05_primitive_jobs_primitive_entertainer.txt` |
| `primitive_warrior_2` | `specialist` | `common/pop_jobs/pif_05_primitive_jobs_primitive_warrior_2.txt` |
| `primitive_bureaucrat` | `ruler` | `common/pop_jobs/pif_05_primitive_jobs_primitive_bureaucrat.txt` |
| `solarpunk_anarchist` | `ruler` | `common/pop_jobs/pif_05_primitive_jobs_solarpunk_anarchist.txt` |
| `primitive_administrator` | `specialist` | `common/pop_jobs/pif_05_primitive_jobs_primitive_administrator.txt` |
| `hive_sustenance_drone` | `simple_drone` | `common/pop_jobs/pif_05_primitive_jobs_hive_sustenance_drone.txt` |
| `hive_sustenance_drone_lithoid` | `simple_drone` | `common/pop_jobs/pif_05_primitive_jobs_hive_sustenance_drone_lithoid.txt` |
| `hive_basic_agri_drone` | `simple_drone` | `common/pop_jobs/pif_05_primitive_jobs_hive_basic_agri_drone.txt` |
| `hive_basic_agri_drone_lithoid` | `simple_drone` | `common/pop_jobs/pif_05_primitive_jobs_hive_basic_agri_drone_lithoid.txt` |
| `primitive_hive_warrior` | `simple_drone` | `common/pop_jobs/pif_05_primitive_jobs_primitive_hive_warrior.txt` |
| `primitive_hive_synapse_drone` | `complex_drone` | `common/pop_jobs/pif_05_primitive_jobs_primitive_hive_synapse_drone.txt` |
| `primitive_hive_cerebellum_drone` | `complex_drone` | `common/pop_jobs/pif_05_primitive_jobs_primitive_hive_cerebellum_drone.txt` |
| `primitive_hive_factory_drone` | `simple_drone` | `common/pop_jobs/pif_05_primitive_jobs_primitive_hive_factory_drone.txt` |
| `primitive_hive_miner` | `simple_drone` | `common/pop_jobs/pif_05_primitive_jobs_primitive_hive_miner.txt` |
| `primitive_hive_technician` | `simple_drone` | `common/pop_jobs/pif_05_primitive_jobs_primitive_hive_technician.txt` |
| `primitive_hive_farmer` | `simple_drone` | `common/pop_jobs/pif_05_primitive_jobs_primitive_hive_farmer.txt` |
| `primitive_hive_brain_drone` | `complex_drone` | `common/pop_jobs/pif_05_primitive_jobs_primitive_hive_brain_drone.txt` |
| `primitive_hive_spawning_drone` | `complex_drone` | `common/pop_jobs/pif_05_primitive_jobs_primitive_hive_spawning_drone.txt` |
| `primitive_hive_warrior_2` | `simple_drone` | `common/pop_jobs/pif_05_primitive_jobs_primitive_hive_warrior_2.txt` |
| `primitive_hive_synapse_drone_2` | `complex_drone` | `common/pop_jobs/pif_05_primitive_jobs_primitive_hive_synapse_drone_2.txt` |

### `pop_jobs/06_event_jobs.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `event_purge` | `special_other` | `common/pop_jobs/pif_06_event_jobs_event_purge.txt` |
| `ratling_scavenger` | `worker` | `common/pop_jobs/pif_06_event_jobs_ratling_scavenger.txt` |
| `odd_factory_worker` | `worker` | `common/pop_jobs/pif_06_event_jobs_odd_factory_worker.txt` |
| `odd_factory_drone` | `simple_drone` | `common/pop_jobs/pif_06_event_jobs_odd_factory_drone.txt` |
| `underground_trade_worker` | `specialist` | `common/pop_jobs/pif_06_event_jobs_underground_trade_worker.txt` |
| `underground_contact_drone` | `simple_drone` | `common/pop_jobs/pif_06_event_jobs_underground_contact_drone.txt` |
| `dimensional_portal_researcher` | `specialist` | `common/pop_jobs/pif_06_event_jobs_dimensional_portal_researcher.txt` |
| `dimensional_portal_researcher_gestalt` | `complex_drone` | `common/pop_jobs/pif_06_event_jobs_dimensional_portal_researcher_gestalt.txt` |
| `space_time_anomaly_researcher` | `specialist` | `common/pop_jobs/pif_06_event_jobs_space_time_anomaly_researcher.txt` |
| `space_time_anomaly_researcher_gestalt` | `complex_drone` | `common/pop_jobs/pif_06_event_jobs_space_time_anomaly_researcher_gestalt.txt` |
| `gas_plant_engineer` | `specialist` | `common/pop_jobs/pif_06_event_jobs_gas_plant_engineer.txt` |
| `gas_plant_engineer_gestalt` | `complex_drone` | `common/pop_jobs/pif_06_event_jobs_gas_plant_engineer_gestalt.txt` |
| `cave_cleaner` | `no_category` | `common/pop_jobs/pif_06_event_jobs_cave_cleaner.txt` |
| `cave_cleaner_gestalt` | `simple_drone` | `common/pop_jobs/pif_06_event_jobs_cave_cleaner_gestalt.txt` |
| `titan_hunter` | `worker` | `common/pop_jobs/pif_06_event_jobs_titan_hunter.txt` |
| `robot_caretaker` | `specialist` | `common/pop_jobs/pif_06_event_jobs_robot_caretaker.txt` |
| `turtle_miner` | `worker` | `common/pop_jobs/pif_06_event_jobs_turtle_miner.txt` |
| `turtle_miner_gestalt` | `simple_drone` | `common/pop_jobs/pif_06_event_jobs_turtle_miner_gestalt.txt` |
| `machine_nurse` | `special_other` | `common/pop_jobs/pif_06_event_jobs_machine_nurse.txt` |
| `manufactorium_specialist` | `specialist` | `common/pop_jobs/pif_06_event_jobs_manufactorium_specialist.txt` |
| `manufactorium_complex_drone` | `complex_drone` | `common/pop_jobs/pif_06_event_jobs_manufactorium_complex_drone.txt` |
| `manufactorium_scraper` | `no_category` | `common/pop_jobs/pif_06_event_jobs_manufactorium_scraper.txt` |
| `manufactorium_scraper_drone` | `simple_drone` | `common/pop_jobs/pif_06_event_jobs_manufactorium_scraper_drone.txt` |
| `archivist` | `specialist` | `common/pop_jobs/pif_06_event_jobs_archivist.txt` |
| `puddle_technician` | `worker` | `common/pop_jobs/pif_06_event_jobs_puddle_technician.txt` |
| `puddle_technician_drone` | `simple_drone` | `common/pop_jobs/pif_06_event_jobs_puddle_technician_drone.txt` |
| `stasis_warden` | `specialist` | `common/pop_jobs/pif_06_event_jobs_stasis_warden.txt` |
| `stasis_warden_drone` | `complex_drone` | `common/pop_jobs/pif_06_event_jobs_stasis_warden_drone.txt` |
| `astrogarbage_collector` | `worker` | `common/pop_jobs/pif_06_event_jobs_astrogarbage_collector.txt` |
| `astrogarbage_collector_gestalt` | `simple_drone` | `common/pop_jobs/pif_06_event_jobs_astrogarbage_collector_gestalt.txt` |
| `myrmeku_power_farmer` | `specialist` | `common/pop_jobs/pif_06_event_jobs_myrmeku_power_farmer.txt` |
| `myrmeku_power_farmer_gestalt` | `complex_drone` | `common/pop_jobs/pif_06_event_jobs_myrmeku_power_farmer_gestalt.txt` |
| `stratovent_researcher` | `specialist` | `common/pop_jobs/pif_06_event_jobs_stratovent_researcher.txt` |
| `stratovent_refiner` | `specialist` | `common/pop_jobs/pif_06_event_jobs_stratovent_refiner.txt` |
| `stratovent_refiner_upg` | `specialist` | `common/pop_jobs/pif_06_event_jobs_stratovent_refiner_upg.txt` |
| `stratovent_refiner_minerals` | `specialist` | `common/pop_jobs/pif_06_event_jobs_stratovent_refiner_minerals.txt` |
| `mineral_diver` | `no_category` | `common/pop_jobs/pif_06_event_jobs_mineral_diver.txt` |
| `mineral_diver_drone` | `simple_drone` | `common/pop_jobs/pif_06_event_jobs_mineral_diver_drone.txt` |
| `alien_hunter` | `worker` | `common/pop_jobs/pif_06_event_jobs_alien_hunter.txt` |

### `pop_jobs/07_fallen_empire_jobs.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `fe_overseer` | `special_other` | `common/pop_jobs/pif_07_fallen_empire_jobs_fe_overseer.txt` |
| `fe_sky_cardinal` | `special_other` | `common/pop_jobs/pif_07_fallen_empire_jobs_fe_sky_cardinal.txt` |
| `fe_guardian_bot` | `special_other` | `common/pop_jobs/pif_07_fallen_empire_jobs_fe_guardian_bot.txt` |
| `fe_protector` | `special_other` | `common/pop_jobs/pif_07_fallen_empire_jobs_fe_protector.txt` |
| `fe_archivist` | `special_other` | `common/pop_jobs/pif_07_fallen_empire_jobs_fe_archivist.txt` |
| `fe_acolyte_farm` | `special_other` | `common/pop_jobs/pif_07_fallen_empire_jobs_fe_acolyte_farm.txt` |
| `fe_acolyte_mine` | `special_other` | `common/pop_jobs/pif_07_fallen_empire_jobs_fe_acolyte_mine.txt` |
| `fe_acolyte_generator` | `special_other` | `common/pop_jobs/pif_07_fallen_empire_jobs_fe_acolyte_generator.txt` |
| `fe_augur` | `special_other` | `common/pop_jobs/pif_07_fallen_empire_jobs_fe_augur.txt` |
| `fe_xeno_keeper` | `special_other` | `common/pop_jobs/pif_07_fallen_empire_jobs_fe_xeno_keeper.txt` |
| `fe_xeno_ward` | `special_other` | `common/pop_jobs/pif_07_fallen_empire_jobs_fe_xeno_ward.txt` |
| `fe_hedonist` | `special_other` | `common/pop_jobs/pif_07_fallen_empire_jobs_fe_hedonist.txt` |
| `fe_acolyte_artisan` | `special_other` | `common/pop_jobs/pif_07_fallen_empire_jobs_fe_acolyte_artisan.txt` |
| `fe_maintenance_bot` | `special_other` | `common/pop_jobs/pif_07_fallen_empire_jobs_fe_maintenance_bot.txt` |

### `pop_jobs/08_overlord_jobs.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `overlord_propagandist` | `specialist` | `common/pop_jobs/pif_08_overlord_jobs_overlord_propagandist.txt` |
| `overlord_propagandist_drone` | `complex_drone` | `common/pop_jobs/pif_08_overlord_jobs_overlord_propagandist_drone.txt` |
| `overlord_academic` | `specialist` | `common/pop_jobs/pif_08_overlord_jobs_overlord_academic.txt` |
| `overlord_academic_drone` | `complex_drone` | `common/pop_jobs/pif_08_overlord_jobs_overlord_academic_drone.txt` |
| `overlord_trader` | `specialist` | `common/pop_jobs/pif_08_overlord_jobs_overlord_trader.txt` |
| `overlord_trader_drone` | `complex_drone` | `common/pop_jobs/pif_08_overlord_jobs_overlord_trader_drone.txt` |
| `aid_worker` | `worker` | `common/pop_jobs/pif_08_overlord_jobs_aid_worker.txt` |
| `aid_worker_drone` | `simple_drone` | `common/pop_jobs/pif_08_overlord_jobs_aid_worker_drone.txt` |
| `overlord_breeder` | `specialist` | `common/pop_jobs/pif_08_overlord_jobs_overlord_breeder.txt` |
| `overlord_breeder_drone` | `complex_drone` | `common/pop_jobs/pif_08_overlord_jobs_overlord_breeder_drone.txt` |
| `mind_thrall` | `worker` | `common/pop_jobs/pif_08_overlord_jobs_mind_thrall.txt` |
| `mind_thrall_drone` | `simple_drone` | `common/pop_jobs/pif_08_overlord_jobs_mind_thrall_drone.txt` |
| `overlord_offspring_drone_feeder` | `specialist` | `common/pop_jobs/pif_08_overlord_jobs_overlord_offspring_drone_feeder.txt` |
| `overlord_offspring_drone_feeder_drone` | `complex_drone` | `common/pop_jobs/pif_08_overlord_jobs_overlord_offspring_drone_feeder_drone.txt` |
| `overlord_metallurgist` | `specialist` | `common/pop_jobs/pif_08_overlord_jobs_overlord_metallurgist.txt` |
| `overlord_foundry_drone` | `complex_drone` | `common/pop_jobs/pif_08_overlord_jobs_overlord_foundry_drone.txt` |
| `overlord_fabricator` | `complex_drone` | `common/pop_jobs/pif_08_overlord_jobs_overlord_fabricator.txt` |
| `overlord_catalytic_technician` | `specialist` | `common/pop_jobs/pif_08_overlord_jobs_overlord_catalytic_technician.txt` |
| `overlord_catalytic_drone` | `complex_drone` | `common/pop_jobs/pif_08_overlord_jobs_overlord_catalytic_drone.txt` |
| `overlord_beholder` | `specialist` | `common/pop_jobs/pif_08_overlord_jobs_overlord_beholder.txt` |
| `overlord_beholder_drone` | `complex_drone` | `common/pop_jobs/pif_08_overlord_jobs_overlord_beholder_drone.txt` |
| `overlord_necromancer` | `specialist` | `common/pop_jobs/pif_08_overlord_jobs_overlord_necromancer.txt` |
| `overlord_necromancer_drone` | `complex_drone` | `common/pop_jobs/pif_08_overlord_jobs_overlord_necromancer_drone.txt` |
| `overlord_reassigner` | `specialist` | `common/pop_jobs/pif_08_overlord_jobs_overlord_reassigner.txt` |
| `overlord_reassigner_drone` | `complex_drone` | `common/pop_jobs/pif_08_overlord_jobs_overlord_reassigner_drone.txt` |
| `overlord_recruiter` | `specialist` | `common/pop_jobs/pif_08_overlord_jobs_overlord_recruiter.txt` |
| `overlord_recruiter_drone` | `complex_drone` | `common/pop_jobs/pif_08_overlord_jobs_overlord_recruiter_drone.txt` |
| `overlord_ranger` | `worker` | `common/pop_jobs/pif_08_overlord_jobs_overlord_ranger.txt` |
| `overlord_ranger_drone` | `simple_drone` | `common/pop_jobs/pif_08_overlord_jobs_overlord_ranger_drone.txt` |
| `overlord_arborist` | `worker` | `common/pop_jobs/pif_08_overlord_jobs_overlord_arborist.txt` |
| `overlord_arborist_drone` | `simple_drone` | `common/pop_jobs/pif_08_overlord_jobs_overlord_arborist_drone.txt` |
| `overlord_bio_trophy` | `worker` | `common/pop_jobs/pif_08_overlord_jobs_overlord_bio_trophy.txt` |
| `overlord_bio_trophy_drone` | `simple_drone` | `common/pop_jobs/pif_08_overlord_jobs_overlord_bio_trophy_drone.txt` |
| `overlord_manager` | `specialist` | `common/pop_jobs/pif_08_overlord_jobs_overlord_manager.txt` |
| `overlord_mortal_initiate` | `worker` | `common/pop_jobs/pif_08_overlord_jobs_overlord_mortal_initiate.txt` |
| `overlord_mortal_initiate_drone` | `simple_drone` | `common/pop_jobs/pif_08_overlord_jobs_overlord_mortal_initiate_drone.txt` |
| `overlord_knight` | `specialist` | `common/pop_jobs/pif_08_overlord_jobs_overlord_knight.txt` |
| `overlord_knight_drone` | `complex_drone` | `common/pop_jobs/pif_08_overlord_jobs_overlord_knight_drone.txt` |
| `overlord_healthcare` | `specialist` | `common/pop_jobs/pif_08_overlord_jobs_overlord_healthcare.txt` |
| `overlord_replicator` | `complex_drone` | `common/pop_jobs/pif_08_overlord_jobs_overlord_replicator.txt` |
| `overlord_spawning_drone` | `complex_drone` | `common/pop_jobs/pif_08_overlord_jobs_overlord_spawning_drone.txt` |
| `overlord_spawning_drone_lithoid` | `complex_drone` | `common/pop_jobs/pif_08_overlord_jobs_overlord_spawning_drone_lithoid.txt` |

### `pop_jobs/09_first_contact_jobs.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `low_tech_laborer` | `worker` | `common/pop_jobs/pif_09_first_contact_jobs_low_tech_laborer.txt` |
| `low_tech_miner` | `worker` | `common/pop_jobs/pif_09_first_contact_jobs_low_tech_miner.txt` |
| `low_tech_technician` | `worker` | `common/pop_jobs/pif_09_first_contact_jobs_low_tech_technician.txt` |
| `low_tech_farmer` | `worker` | `common/pop_jobs/pif_09_first_contact_jobs_low_tech_farmer.txt` |
| `low_tech_researcher` | `specialist` | `common/pop_jobs/pif_09_first_contact_jobs_low_tech_researcher.txt` |
| `low_tech_priest` | `specialist` | `common/pop_jobs/pif_09_first_contact_jobs_low_tech_priest.txt` |
| `low_tech_bureaucrat` | `specialist` | `common/pop_jobs/pif_09_first_contact_jobs_low_tech_bureaucrat.txt` |
| `low_tech_manager` | `specialist` | `common/pop_jobs/pif_09_first_contact_jobs_low_tech_manager.txt` |
| `low_tech_warrior` | `specialist` | `common/pop_jobs/pif_09_first_contact_jobs_low_tech_warrior.txt` |
| `broken_shackles_scavenger` | `worker` | `common/pop_jobs/pif_09_first_contact_jobs_broken_shackles_scavenger.txt` |

### `pop_jobs/10_paragon_fake_jobs.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `captain` | `no_category` | `common/pop_jobs/pif_10_paragon_fake_jobs_captain.txt` |
| `chief_navigator` | `no_category` | `common/pop_jobs/pif_10_paragon_fake_jobs_chief_navigator.txt` |
| `principal_pilot` | `no_category` | `common/pop_jobs/pif_10_paragon_fake_jobs_principal_pilot.txt` |
| `ship_weapons_officer` | `no_category` | `common/pop_jobs/pif_10_paragon_fake_jobs_ship_weapons_officer.txt` |
| `ship_logistics_officer` | `no_category` | `common/pop_jobs/pif_10_paragon_fake_jobs_ship_logistics_officer.txt` |
| `special_operations_commander` | `no_category` | `common/pop_jobs/pif_10_paragon_fake_jobs_special_operations_commander.txt` |
| `commanding_officer` | `no_category` | `common/pop_jobs/pif_10_paragon_fake_jobs_commanding_officer.txt` |
| `chief_supply_officer` | `no_category` | `common/pop_jobs/pif_10_paragon_fake_jobs_chief_supply_officer.txt` |
| `intelligence_officer` | `no_category` | `common/pop_jobs/pif_10_paragon_fake_jobs_intelligence_officer.txt` |
| `chief_security_officer` | `no_category` | `common/pop_jobs/pif_10_paragon_fake_jobs_chief_security_officer.txt` |
| `government_employee` | `no_category` | `common/pop_jobs/pif_10_paragon_fake_jobs_government_employee.txt` |
| `researcher` | `no_category` | `common/pop_jobs/pif_10_paragon_fake_jobs_researcher.txt` |
| `none` | `no_category` | `common/pop_jobs/pif_10_paragon_fake_jobs_none.txt` |

### `pop_jobs/11_astral_planes_jobs.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `munitions_decommissioner` | `specialist` | `common/pop_jobs/pif_11_astral_planes_jobs_munitions_decommissioner.txt` |
| `munitions_decommissioning_unit` | `complex_drone` | `common/pop_jobs/pif_11_astral_planes_jobs_munitions_decommissioning_unit.txt` |
| `munitions_decommissioning_unit_lithoid` | `complex_drone` | `common/pop_jobs/pif_11_astral_planes_jobs_munitions_decommissioning_unit_lithoid.txt` |
| `munitions_decommissioning_drone` | `complex_drone` | `common/pop_jobs/pif_11_astral_planes_jobs_munitions_decommissioning_drone.txt` |
| `astral_researcher` | `specialist` | `common/pop_jobs/pif_11_astral_planes_jobs_astral_researcher.txt` |
| `astral_drone` | `complex_drone` | `common/pop_jobs/pif_11_astral_planes_jobs_astral_drone.txt` |
| `astral_unit` | `complex_drone` | `common/pop_jobs/pif_11_astral_planes_jobs_astral_unit.txt` |

### `pop_jobs/12_cosmic_storm_jobs.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `astrometeorologist` | `specialist` | `common/pop_jobs/pif_12_cosmic_storm_jobs_astrometeorologist.txt` |
| `astrometeorologist_hive` | `complex_drone` | `common/pop_jobs/pif_12_cosmic_storm_jobs_astrometeorologist_hive.txt` |
| `astrometeorologist_machine` | `complex_drone` | `common/pop_jobs/pif_12_cosmic_storm_jobs_astrometeorologist_machine.txt` |

### `pop_jobs/13_machine_age_jobs.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `haruspex` | `specialist` | `common/pop_jobs/pif_13_machine_age_jobs_haruspex.txt` |
| `technophant` | `ruler` | `common/pop_jobs/pif_13_machine_age_jobs_technophant.txt` |
| `neural_chip` | `special_other` | `common/pop_jobs/pif_13_machine_age_jobs_neural_chip.txt` |
| `neural_chip_processing` | `special_other` | `common/pop_jobs/pif_13_machine_age_jobs_neural_chip_processing.txt` |
| `neural_chip_unprocessing` | `special_other` | `common/pop_jobs/pif_13_machine_age_jobs_neural_chip_unprocessing.txt` |
| `augmentor` | `specialist` | `common/pop_jobs/pif_13_machine_age_jobs_augmentor.txt` |
| `augmentor_drone` | `complex_drone` | `common/pop_jobs/pif_13_machine_age_jobs_augmentor_drone.txt` |
| `identity_designer` | `specialist` | `common/pop_jobs/pif_13_machine_age_jobs_identity_designer.txt` |
| `cyberdome_duelist` | `specialist` | `common/pop_jobs/pif_13_machine_age_jobs_cyberdome_duelist.txt` |
| `cyberdome_spectator` | `worker` | `common/pop_jobs/pif_13_machine_age_jobs_cyberdome_spectator.txt` |
| `clip_maximizer` | `special_other` | `common/pop_jobs/pif_13_machine_age_jobs_clip_maximizer.txt` |
| `nanotech_research_unit` | `complex_drone` | `common/pop_jobs/pif_13_machine_age_jobs_nanotech_research_unit.txt` |
| `nanotech_researcher` | `specialist` | `common/pop_jobs/pif_13_machine_age_jobs_nanotech_researcher.txt` |

### `pop_jobs/14_grand_archive_jobs.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `treasure_gatherer` | `specialist` | `common/pop_jobs/pif_14_grand_archive_jobs_treasure_gatherer.txt` |
| `wrangler` | `specialist` | `common/pop_jobs/pif_14_grand_archive_jobs_wrangler.txt` |
| `drone_wrangler` | `complex_drone` | `common/pop_jobs/pif_14_grand_archive_jobs_drone_wrangler.txt` |
| `treasure_gatherer_gestalt` | `complex_drone` | `common/pop_jobs/pif_14_grand_archive_jobs_treasure_gatherer_gestalt.txt` |

### `pop_jobs/15_biogenesis_jobs.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `disconnected_drone` | `simple_drone` | `common/pop_jobs/pif_15_biogenesis_jobs_disconnected_drone.txt` |
| `skywatcher` | `specialist` | `common/pop_jobs/pif_15_biogenesis_jobs_skywatcher.txt` |
| `skywatcher_drone` | `complex_drone` | `common/pop_jobs/pif_15_biogenesis_jobs_skywatcher_drone.txt` |
| `genomic_researcher` | `specialist` | `common/pop_jobs/pif_15_biogenesis_jobs_genomic_researcher.txt` |
| `genomic_drone` | `complex_drone` | `common/pop_jobs/pif_15_biogenesis_jobs_genomic_drone.txt` |
| `transference_volunteer` | `specialist` | `common/pop_jobs/pif_15_biogenesis_jobs_transference_volunteer.txt` |
| `transference_drone` | `complex_drone` | `common/pop_jobs/pif_15_biogenesis_jobs_transference_drone.txt` |

### `pop_jobs/15_gestalt_unemployment.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `complex_drone_unemployment` | `special_other` | `common/pop_jobs/pif_15_gestalt_unemployment_complex_drone_unemployment.txt` |
| `simple_drone_unemployment` | `special_other` | `common/pop_jobs/pif_15_gestalt_unemployment_simple_drone_unemployment.txt` |

### `pop_jobs/15_strange_worlds_jobs.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `sand_whisperer` | `specialist` | `common/pop_jobs/pif_15_strange_worlds_jobs_sand_whisperer.txt` |
| `sand_caretaker` | `specialist` | `common/pop_jobs/pif_15_strange_worlds_jobs_sand_caretaker.txt` |
| `drone_sand_whisperer` | `complex_drone` | `common/pop_jobs/pif_15_strange_worlds_jobs_drone_sand_whisperer.txt` |
| `drone_sand_caretaker` | `complex_drone` | `common/pop_jobs/pif_15_strange_worlds_jobs_drone_sand_caretaker.txt` |
| `space_junk_collector` | `specialist` | `common/pop_jobs/pif_15_strange_worlds_jobs_space_junk_collector.txt` |
| `drone_space_junk_collector` | `complex_drone` | `common/pop_jobs/pif_15_strange_worlds_jobs_drone_space_junk_collector.txt` |

### `pop_jobs/15_unemployment.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `ruler_unemployment` | `special_other` | `common/pop_jobs/pif_15_unemployment_ruler_unemployment.txt` |
| `specialist_unemployment` | `special_other` | `common/pop_jobs/pif_15_unemployment_specialist_unemployment.txt` |
| `worker_unemployment` | `special_other` | `common/pop_jobs/pif_15_unemployment_worker_unemployment.txt` |
| `bio_trophy_unemployment` | `special_other` | `common/pop_jobs/pif_15_unemployment_bio_trophy_unemployment.txt` |
| `slave_unemployment` | `special_other` | `common/pop_jobs/pif_15_unemployment_slave_unemployment.txt` |

### `pop_jobs/16_shroud_jobs.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `telepath_drone` | `complex_drone` | `common/pop_jobs/pif_16_shroud_jobs_telepath_drone.txt` |
| `physician_drone` | `complex_drone` | `common/pop_jobs/pif_16_shroud_jobs_physician_drone.txt` |
| `observator_drone` | `complex_drone` | `common/pop_jobs/pif_16_shroud_jobs_observator_drone.txt` |
| `energy_thrall` | `worker` | `common/pop_jobs/pif_16_shroud_jobs_energy_thrall.txt` |
| `drone_energy_thrall` | `simple_drone` | `common/pop_jobs/pif_16_shroud_jobs_drone_energy_thrall.txt` |
| `test_subject` | `special_other` | `common/pop_jobs/pif_16_shroud_jobs_test_subject.txt` |
| `test_subject_drone` | `special_other` | `common/pop_jobs/pif_16_shroud_jobs_test_subject_drone.txt` |
| `experiment_engineer` | `specialist` | `common/pop_jobs/pif_16_shroud_jobs_experiment_engineer.txt` |
| `experiment_engineer_drone` | `complex_drone` | `common/pop_jobs/pif_16_shroud_jobs_experiment_engineer_drone.txt` |
| `slave_orderly` | `worker` | `common/pop_jobs/pif_16_shroud_jobs_slave_orderly.txt` |
| `production_overseer` | `specialist` | `common/pop_jobs/pif_16_shroud_jobs_production_overseer.txt` |
| `spe_colonist` | `specialist` | `common/pop_jobs/pif_16_shroud_jobs_spe_colonist.txt` |
| `extradimensional_research_unit` | `complex_drone` | `common/pop_jobs/pif_16_shroud_jobs_extradimensional_research_unit.txt` |
| `shroud_trader` | `specialist` | `common/pop_jobs/pif_16_shroud_jobs_shroud_trader.txt` |

### `pop_jobs/99_swap_jobs.txt`

| Object | Class | PIF file |
| --- | --- | --- |
| `duelist` | `specialist` | `common/pop_jobs/pif_99_swap_jobs_duelist.txt` |
| `historical_curator` | `specialist` | `common/pop_jobs/pif_99_swap_jobs_historical_curator.txt` |
| `storm_dancer` | `specialist` | `common/pop_jobs/pif_99_swap_jobs_storm_dancer.txt` |

## Source files and documentation used

| Type | Files |
| --- | --- |
| Vanilla object files | `common/pop_jobs/*.txt` |
| Inline scripts | reachable files under `common/inline_scripts/` |
| Scripted variables | `common/scripted_variables/*.txt` |
| Object documentation | `common/pop_jobs/000_pretriggers.txt` and actual `common/pop_jobs` objects |
| Generated reports | `Analytics/reports/jobs/` |
