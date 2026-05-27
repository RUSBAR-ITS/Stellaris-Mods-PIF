# PIF tooling — technical documentation

## Table of Contents

- [Document purpose](#document-purpose)
- [Tooling purpose](#tooling-purpose)
- [Pipeline model](#pipeline-model)
  - [Profile](#profile)
  - [Backend](#backend)
  - [Category inline scripts](#category-inline-scripts)
  - [Variable domains](#variable-domains)
  - [Static validation](#static-validation)
- [build-scripts layout](#build-scripts-layout)
- [Supported profiles](#supported-profiles)
- [Inputs](#inputs)
- [Outputs](#outputs)
- [Command reference](#command-reference)
  - [`pif_analyze.py`](#pif_analyzepy)
  - [`pif_split_inline_scripts.py`](#pif_split_inline_scriptspy)
  - [`pif_generate_layer.py`](#pif_generate_layerpy)
  - [`pif_validate_layer.py`](#pif_validate_layerpy)
  - [`pif_run_all.py`](#pif_run_allpy)
- [Quick run](#quick-run)
- [Inline script rules](#inline-script-rules)
- [Scripted variable rules](#scripted-variable-rules)
- [Order and AST comparison rules](#order-and-ast-comparison-rules)
- [Profile-specific behavior](#profile-specific-behavior)
  - [`districts`](#districts)
  - [`zones`](#zones)
  - [`zone_slots`](#zone_slots)
  - [`buildings`](#buildings)
  - [`jobs`](#jobs)
- [Pipeline control metrics](#pipeline-control-metrics)
- [Reports and manifests](#reports-and-manifests)
- [Adding a new profile](#adding-a-new-profile)
- [Updating rules for a changed vanilla baseline](#updating-rules-for-a-changed-vanilla-baseline)
- [Troubleshooting](#troubleshooting)

## Document purpose

This document describes the current analysis, generation and validation tooling used by Planetary Infrastructure Framework.

It defines how to use `build-scripts`, which profiles are supported, which files are generated, which checks are performed, and which technical decisions are encoded in the pipeline. It describes the current working behavior of the tools, not their development history.

## Tooling purpose

PIF tooling exists to build the framework layer reproducibly from a vanilla baseline. The scripts do not make balance decisions and do not manually improve vanilla objects. Their job is to move vanilla behavior into the PIF architecture and verify that expanded PIF remains equivalent to expanded vanilla after explicitly allowed normalizations.

The pipeline performs five tasks:

1. Load the vanilla baseline from `Planet.zip` or an extracted folder.
2. Expand `inline_script` recursively.
3. Analyze actual object parameters after expansion.
4. Generate the normalized PIF layer: one object file per vanilla object, category inline scripts, and scripted variables.
5. Run static validation against the vanilla baseline.

## Pipeline model

### Profile

A `Profile` describes one object family handled by the shared CLI tools. Profiles are registered in `pif_profiles.py`.

A profile defines:

- CLI profile name;
- vanilla source folder;
- generated output folder;
- object label;
- object prefix, when applicable;
- canonical categories;
- parameter classification function;
- statement-level normalization function;
- generation backend;
- validation backend;
- generation manifest name;
- validation report name.

Supported profiles:

```txt
buildings
districts
jobs
zone_slots
zones
```

### Backend

A `Backend` is a profile-specific module under `pif_backends/`. The CLI commands are shared across all profiles, while backend modules contain the rules for each object family.

Backends are needed because object layers differ structurally:

- `districts` distinguish real districts and district masks;
- `zones` contain building compatibility and `swap_type` logic;
- `zone_slots` are structural containers for zones;
- `buildings` require semantic splitting of modifier-carrier blocks;
- `jobs` require dedicated handling for job flags, `resources`, `overlord_resources`, weights and modifier blocks.

### Category inline scripts

A category inline script is a PIF-owned file containing one semantic part of an object.

Example:

```txt
common/inline_scripts/pif/buildings/building_research_lab_1/economy.txt
common/inline_scripts/pif/jobs/researcher/weight.txt
common/inline_scripts/pif/zones/zone_research/availability.txt
```

Category scripts reduce the conflict surface between mods. A mod that changes only object economy should not need to replace the entire object file.

### Variable domains

A variable domain is a semantic category of values under `common/scripted_variables`.

Variable domains do not have to match object categories. Object categories answer “where does this part of the object live”, while variable domains answer “what does this value control”. For example, `base_buildtime` can remain in the root object while its variable belongs to the construction domain.

General rules:

- vanilla `@variables` are resolved to concrete values;
- PIF variables are object-specific;
- aliases like `@pif_x = @pif_y` are not created;
- `value:` expressions are not converted to PIF variables;
- nested trigger booleans normally remain literal;
- top-level job boolean flags are intentionally converted to job flag variables.

### Static validation

Static validation compares the expanded vanilla object with the expanded generated PIF object.

The validator expands PIF category inline scripts, resolves generated PIF variables, applies allowed profile normalizations, and compares canonical representations. This is a structural equivalence check; it does not replace in-game testing.

## build-scripts layout

```txt
build-scripts/
  pif_stellaris.py
  pif_profiles.py
  pif_analyze.py
  pif_split_inline_scripts.py
  pif_generate_layer.py
  pif_validate_layer.py
  pif_run_all.py
  pif_backends/
    __init__.py
    districts_generate.py
    districts_validate.py
    zones_generate.py
    zones_validate.py
    zone_slots_generate.py
    zone_slots_validate.py
    buildings_common.py
    buildings_generate.py
    buildings_validate.py
    jobs_common.py
    jobs_generate.py
    jobs_validate.py
```

| File | Purpose |
|---|---|
| `pif_stellaris.py` | Parser, renderer, loader, inline expansion, shared AST helpers. |
| `pif_profiles.py` | Profile registry and dispatch settings. |
| `pif_analyze.py` | Vanilla object analysis for one profile. |
| `pif_split_inline_scripts.py` | Reachable vanilla inline script analysis and split requirements. |
| `pif_generate_layer.py` | PIF layer generation for one profile. |
| `pif_validate_layer.py` | Static validation of the generated layer. |
| `pif_run_all.py` | Full pipeline in one command. |
| `pif_backends/*` | Profile-specific generation, classification, variable handling and validation. |

## Supported profiles

| Profile | Vanilla source folder | Generated folder | Object label | Backend modules |
|---|---|---|---|---|
| `districts` | `common/districts` | `common/districts` | district | `districts_generate.py`, `districts_validate.py` |
| `zones` | `common/zones` | `common/zones` | zone | `zones_generate.py`, `zones_validate.py` |
| `zone_slots` | `common/zone_slots` | `common/zone_slots` | zone slot | `zone_slots_generate.py`, `zone_slots_validate.py` |
| `buildings` | `common/buildings` | `common/buildings` | building | `buildings_common.py`, `buildings_generate.py`, `buildings_validate.py` |
| `jobs` | `common/pop_jobs` | `common/pop_jobs` | job | `jobs_common.py`, `jobs_generate.py`, `jobs_validate.py` |

## Inputs

The tools accept the vanilla baseline in two forms:

```txt
--planet /path/to/Planet.zip
--planet /path/to/extracted/Planet
```

`Planet.zip` is extracted into a work directory. Use `--work-dir` to control the extraction location.

The baseline is expected to contain the required vanilla folders and dependent `inline_scripts` / `scripted_variables`. If the baseline is incomplete, analysis or validation can report missing inline scripts, missing objects, or unresolved variables.

## Outputs

The pipeline creates two kinds of outputs:

1. Runtime layer: generated PIF files that can be placed in the mod.
2. Reports: CSV/JSON files for review and validation.

Typical generated structure:

```txt
<out>/
  common/
    districts/
    zones/
    zone_slots/
    buildings/
    pop_jobs/
    inline_scripts/pif/
    scripted_variables/
  pif_<profile>_generation_manifest.json
  pif_<profile>_validation_report.json
```

Reports are written separately, usually under `<reports>/<profile>/`:

```txt
analysis/
inline_scripts/
<profile>_run_all_summary.json
```

## Command reference

All commands share common arguments:

| Argument | Required | Purpose |
|---|---|---|
| `--profile` | yes, except internal helper calls | One of `districts`, `zones`, `zone_slots`, `buildings`, `jobs`. |
| `--planet` | no, but normally needed | Path to `Planet.zip` or an extracted baseline. |
| `--work-dir` | no | Directory used for zip extraction. |

### `pif_analyze.py`

Analyzes vanilla objects for one profile after recursive inline expansion.

```bash
python pif_analyze.py \
  --profile buildings \
  --planet /path/to/Planet.zip \
  --out /path/to/reports/buildings/analysis
```

Outputs:

| File | Contents |
|---|---|
| `<profile>_objects.csv` | Object key, class, source file, source stem, top-level params after expansion. |
| `<profile>_parameters_after_expansion.csv` | Parameter usage after expansion, including class breakdown. |
| `<profile>_reachable_inline_scripts.csv` | Reachable inline scripts, object count, call count, objects. |
| `<profile>_analysis_summary.json` | Analysis summary. |

### `pif_split_inline_scripts.py`

Analyzes reachable vanilla inline scripts for one profile.

```bash
python pif_split_inline_scripts.py \
  --profile jobs \
  --planet /path/to/Planet.zip \
  --out /path/to/reports/jobs/inline_scripts
```

Each reachable inline script is classified as:

| Decision | Meaning |
|---|---|
| `WHOLE` | After expansion, the script belongs to one category or to a metadata-only fragment. |
| `SPLIT` | The script mixes different category owners and must be split into PIF categories. |

For `buildings` and `jobs`, classification uses profile-specific semantic split helpers because modifier-carrier blocks are categorized by their contents.

Outputs:

| File | Contents |
|---|---|
| `<profile>_inline_scripts_summary.csv` | Inline script, decision, categories, parameters, counters. |
| `<profile>_inline_direct_calls.csv` | Direct inline calls from root object bodies. |
| `<profile>_inline_nested_edges.csv` | Nested inline script edges. |
| `<profile>_inline_script_split_summary.json` | Reachable/whole/split summary. |

### `pif_generate_layer.py`

Generates the PIF layer for one profile.

```bash
python pif_generate_layer.py \
  --profile zones \
  --planet /path/to/Planet.zip \
  --out /path/to/generated/zones \
  --clean
```

Arguments:

| Argument | Purpose |
|---|---|
| `--out` | Generated PIF root. If omitted, the profile default output is used. |
| `--clean` | Delete the output directory before generation. |
| `--sparse-empty` | For profiles that support it, skip empty category scripts. |

`--sparse-empty` is dispatched for `zones`, `buildings` and `jobs`. For `districts` and `zone_slots`, empty extension hooks are part of the specification and are not skipped.

### `pif_validate_layer.py`

Validates a generated layer against the vanilla baseline.

```bash
python pif_validate_layer.py \
  --profile buildings \
  --planet /path/to/Planet.zip \
  --generated /path/to/generated/buildings \
  --out /path/to/generated/buildings/pif_building_validation_report.json
```

Arguments:

| Argument | Purpose |
|---|---|
| `--generated` | Generated PIF root. |
| `--out` | JSON validation report path. If omitted, the profile report name is used inside the generated root. |

The validator returns a summary with `checked`, `ok`, `failed`, `warnings` when provided by the backend, and the report path.

### `pif_run_all.py`

Runs the full pipeline:

1. `pif_analyze.py` logic;
2. `pif_split_inline_scripts.py` logic;
3. `pif_generate_layer.py` logic;
4. `pif_validate_layer.py` logic.

```bash
python pif_run_all.py \
  --profile jobs \
  --planet /path/to/Planet.zip \
  --out /path/to/generated/jobs \
  --reports /path/to/reports \
  --clean
```

`pif_run_all.py` writes the final summary to:

```txt
<reports>/<profile>/<profile>_run_all_summary.json
```

## Quick run

Run all profiles separately:

```bash
for profile in districts zones zone_slots buildings jobs; do
  python pif_run_all.py \
    --profile "$profile" \
    --planet /path/to/Planet.zip \
    --out "/path/to/generated/$profile" \
    --reports /path/to/reports \
    --clean
done
```

When building one shared runtime mod output, use the same output root and apply `--clean` only to the first profile:

```bash
python pif_run_all.py --profile districts  --planet /path/to/Planet.zip --out /path/to/PIF --reports /path/to/reports --clean
python pif_run_all.py --profile zones      --planet /path/to/Planet.zip --out /path/to/PIF --reports /path/to/reports
python pif_run_all.py --profile zone_slots --planet /path/to/Planet.zip --out /path/to/PIF --reports /path/to/reports
python pif_run_all.py --profile buildings  --planet /path/to/Planet.zip --out /path/to/PIF --reports /path/to/reports
python pif_run_all.py --profile jobs       --planet /path/to/Planet.zip --out /path/to/PIF --reports /path/to/reports
```

If `--clean` is used after the first profile in a shared output root, it deletes files generated by earlier profiles.

## Inline script rules

Vanilla inline scripts are source material. They are expanded, analyzed and transformed into PIF-owned category inline scripts.

`WHOLE` classification does not require keeping a runtime reference to the vanilla script. It means that, after expansion, the script belongs to a single category and can be moved as one semantic fragment. `SPLIT` means the script mixes several category owners and must be decomposed.

For `buildings` and `jobs`, statement category is not always determined by top-level key. Modifier-carrier parameters such as `triggered_planet_modifier` are classified by block contents. If one modifier block mixes multiple semantic groups, it is not split line-by-line and remains in fallback `TPM`.

## Scripted variable rules

The tools create PIF variables only according to profile-specific rules.

General rules:

- variables are grouped by domain file;
- variables are grouped by object key inside each file;
- vanilla `@variables` are resolved to concrete values;
- generated PIF variables do not reference other PIF variables;
- `value:` scripted value expressions remain expressions;
- localization-selector constants are not variables;
- structural identity values normally remain literal;
- nested trigger booleans are not variables;
- top-level job boolean flags are written to `pif_jobs_flags_variables.txt`.

## Order and AST comparison rules

The parser and renderer preserve statement order. This matters because some vanilla structures are order-sensitive.

Rules:

- `inline_script` is expanded at its call site;
- repeated `triggered_*` blocks are not sorted;
- `convert_to`, `upgrades`, `zone_slots`, building filters and job `weight` lists preserve order;
- validation does not use unconditional alphabetical sorting where order can change behavior;
- canonical comparison happens only after profile-specific normalizations.

## Profile-specific behavior

### `districts`

The `districts` layer distinguishes real districts and district masks.

Real districts use the full schema:

```txt
METADATA + ZONE_SLOTS + AVAILABILITY + ECONOMIC + TPM + LIFECYCLE + AI
```

District masks remain compact:

```txt
METADATA + MASK
```

Behavior:

- `planet_modifier` is normalized into `triggered_planet_modifier`;
- masks do not receive functional economy, lifecycle or AI hooks;
- localization selectors are not variables;
- the variable layer uses domain-specific district variables.

### `zones`

The `zones` layer connects district/zone infrastructure, building compatibility and visual district masks.

Schema:

```txt
METADATA + AVAILABILITY + ZONE_CONFIG + ECONOMY + TPM + LIFECYCLE + AI
```

Behavior:

- `swap_type` and `swap_type_weight` remain in root metadata;
- `zone_sets`, `include`, `excluded_building_sets` and related filters belong to `ZONE_CONFIG`;
- static modifiers are normalized into triggered equivalents;
- variables are grouped by semantic domains, including job-family domains.

### `zone_slots`

The `zone_slots` layer is a structural container for allowed zones.

Schema:

```txt
METADATA + ZS_CONFIG + AVAILABILITY
```

Behavior:

- `start` remains in the root object;
- `include`, `exclude`, `included_zone_sets`, `excluded_zone_sets` go to `ZS_CONFIG`;
- `potential` and `unlock` go to `AVAILABILITY`;
- vanilla zone slots do not use inline scripts;
- no variables are generated.

### `buildings`

The `buildings` layer loads all top-level objects from `common/buildings`, not only keys with the `building_` prefix.

Object classes:

```txt
regular
capital
branch
holding
special
```

Behavior:

- branch office buildings and holdings have distinct structure;
- non-`building_` objects are preserved;
- modifier carriers are classified by contents;
- mixed modifier blocks remain in `TPM`;
- meaningful numeric tuning values become object-specific building variables;
- boolean flags do not become building variables.

### `jobs`

The `jobs` layer loads all top-level objects from `common/pop_jobs`, including jobs without a `category` field.

Object classes:

```txt
ruler
specialist
worker
complex_drone
simple_drone
special_other
no_category
```

Behavior:

- `resources` and `overlord_resources` are job economy;
- `weight`, `promotion`, `demotion`, `swappable_data`, `possible_precalc` and `auto_trait_prio` have profile-specific handling;
- modifier carriers are classified by contents;
- `planet_modifier` and `country_modifier` are normalized into triggered equivalents;
- top-level job boolean flags intentionally become variables;
- nested boolean logic inside triggers remains literal.

## Pipeline control metrics

Control metrics are used as smoke checks after tool or baseline changes. A changed number is not automatically an error, but it must be explained by input data or profile-rule changes.

| Profile | Objects | Reachable inline scripts | WHOLE | SPLIT | Category scripts | Variables | Variable files | Validation |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `districts` | 138 | 47 | 45 | 2 | 348 | 553 | 10 | 138 / 138 OK |
| `zones` | 120 | 39 | 19 | 20 | 720 | 1553 | 14 | 120 / 120 OK |
| `zone_slots` | 27 | 0 | 0 | 0 | 54 | 0 | 0 | 27 / 27 OK |
| `buildings` | 490 | 54 | 42 | 12 | 5390 | 5881 | 12 | 490 / 490 OK |
| `jobs` | 373 | 27 | 17 | 10 | 3357 | 2682 | 12 | 373 / 373 OK |

## Reports and manifests

### Analysis reports

```txt
<reports>/<profile>/analysis/<profile>_objects.csv
<reports>/<profile>/analysis/<profile>_parameters_after_expansion.csv
<reports>/<profile>/analysis/<profile>_reachable_inline_scripts.csv
<reports>/<profile>/analysis/<profile>_analysis_summary.json
```

### Inline script reports

```txt
<reports>/<profile>/inline_scripts/<profile>_inline_scripts_summary.csv
<reports>/<profile>/inline_scripts/<profile>_inline_direct_calls.csv
<reports>/<profile>/inline_scripts/<profile>_inline_nested_edges.csv
<reports>/<profile>/inline_scripts/<profile>_inline_script_split_summary.json
```

### Generation manifests

Generation manifests are written into the generated root and record created object files, category scripts, variables and backend warnings.

Typical names:

```txt
pif_district_generation_manifest.json
pif_zone_generation_manifest.json
pif_zone_slot_generation_manifest.json
pif_building_generation_manifest.json
pif_job_generation_manifest.json
```

### Validation reports

Validation reports are written into the generated root when `--out` is not explicitly supplied.

Typical names:

```txt
pif_district_validation_report.json
pif_zone_validation_report.json
pif_zone_slot_validation_report.json
pif_building_validation_report.json
pif_job_validation_report.json
```

## Adding a new profile

Minimal procedure:

1. Add the object-family loader to `pif_stellaris.py` or a dedicated helper.
2. Define categories and category display names.
3. Add a profile entry to `pif_profiles.py`.
4. Add a generation backend under `pif_backends/<profile>_generate.py`.
5. Add a validation backend under `pif_backends/<profile>_validate.py`.
6. If parameter classification depends on block contents, add shared helpers under `pif_backends/<profile>_common.py`.
7. Run `pif_analyze.py`.
8. Review inline scripts with `pif_split_inline_scripts.py`.
9. Implement generation and variable allocation.
10. Implement static validation.
11. Run `pif_run_all.py`.

A new profile should not require cloned CLI scripts. Shared commands should continue to work through profile/backend dispatch.

## Updating rules for a changed vanilla baseline

Procedure:

1. Replace the vanilla baseline input.
2. Run `pif_analyze.py` for every profile.
3. Compare new parameters with the current specification.
4. Run `pif_split_inline_scripts.py` and review new `SPLIT` or unknown cases.
5. Update category mapping, normalization and variable domains if vanilla changed.
6. Run generation.
7. Run validation.
8. Check the in-game runtime log.

If validation passes but runtime logs show errors, check first:

- block order;
- unresolved scripted variables;
- context-sensitive inline script placement;
- modifier normalization;
- mixed modifier blocks;
- `value:` expressions.

## Troubleshooting

| Symptom | What to check |
|---|---|
| `Unknown PIF profile` | Profile name must be one of `districts`, `zones`, `zone_slots`, `buildings`, `jobs`. |
| `inline_script not found` | Baseline is incomplete or vanilla script path changed. |
| `missing generated object` | Loader/generator did not create the object or the wrong output root is being validated. |
| `expanded body differs` | Category split, normalization, variable replacement or order-sensitive placement is wrong. |
| In-game `Unknown variable` | Check generated `common/scripted_variables` and references in category scripts. |
| In-game `Object with key already exists` | Expected PIF override message if it points to a generated PIF object. |
| `SPLIT` scripts increased sharply | Review new vanilla inline scripts and modifier-carrier classification. |
| Variable count changed | Check variable domains, deduplication and new scalar values in the baseline. |
| Jobs are not filled in-game | Check `possible_pre_triggers`, `possible_precalc`, `possible`, `weight`, top-level flags and `weight` block order. |
