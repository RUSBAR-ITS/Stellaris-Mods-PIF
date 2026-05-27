# Planetary Infrastructure Framework

**Planetary Infrastructure Framework (PIF)** is a Stellaris modding framework that reorganizes the planetary infrastructure layer so modders can make more targeted changes and reduce conflicts with each other.

PIF is built from the vanilla Stellaris **4.3.7** files and is intended to preserve vanilla gameplay behavior.

For regular players, PIF should not change gameplay by itself. Its main purpose is to serve as a dependency and technical foundation for other mods.

## Project idea

While working on Stellaris mods, I kept running into the same problem: even a small change often requires overwriting a large vanilla object.

If you want to change a building cost, the number of jobs it provides, an availability condition, a pop job weight, or one specific modifier, you usually have to copy and overwrite the whole object. When several mods do this at the same time, they conflict even when they are changing completely different parts of the logic.

This leads to complex compatibility patches, and simple balance mods become harder to maintain than they should be.

PIF was created as an attempt to make this work easier: to narrow the most likely conflict points and move meaningful values into separate variables, so they can be changed without touching large objects.

The basic idea of the framework is:

- large vanilla objects are split into smaller semantic parts;
- each such part is moved into a separate inline script;
- meaningful numeric values and some important logical values are moved into scripted variables;
- a modder can change one specific aspect of an object without overwriting the entire object.

In other words, PIF creates an intermediate layer between vanilla Stellaris and mods that want to modify planetary infrastructure.

## Purpose

Planetary Infrastructure Framework is intended primarily for modders who want to modify Stellaris planetary infrastructure in a cleaner and more compatible way.

The framework covers the following object types:

- `districts`;
- `zones`;
- `zone_slots`;
- `buildings`;
- `pop_jobs`.

Each object preserves its vanilla behavior, but its contents are organized into semantic categories.

For example, for buildings it is possible to modify separately:

- cost and upkeep;
- jobs;
- availability conditions;
- lifecycle logic;
- planet modifiers;
- country modifiers;
- pop/job modifiers;
- AI logic.

For jobs it is possible to modify separately:

- production and upkeep;
- pop assignment weights;
- promotion/demotion;
- automation flags;
- top-level job flags;
- planet/country/pop modifiers;
- overlord resources.

This makes it possible to create smaller mods that affect only the needed logic layer instead of overwriting a full vanilla object.

## What the framework does

PIF:

- overwrites vanilla planetary infrastructure objects;
- preserves vanilla behavior;
- splits objects into small semantic inline scripts;
- moves meaningful values into scripted variables;
- creates stable extension points for other mods;
- reduces the likelihood of conflicts between mods built on top of PIF.

PIF is not a balance mod. Its goal is not to change the game, but to provide a convenient technical foundation for other mods.

## Compatibility

PIF is fundamentally incompatible with mods that directly modify the same vanilla files used as the framework baseline.

The list of affected vanilla files and objects is available here:

[docs/AFFECTED_VANILLA_FILES.md](docs/AFFECTED_VANILLA_FILES.md)

If another mod directly overwrites objects from these files, it will most likely conflict with PIF.

The main idea of the framework is important here: PIF is not trying to be compatible with every mod that rewrites the same vanilla objects. Its goal is to provide a foundation that other mods can build on so they conflict with each other much less often.

In practice:

- mods that directly overwrite the same `districts`, `zones`, `zone_slots`, `buildings`, or `pop_jobs` may conflict with PIF;
- mods that use PIF inline scripts and PIF variables should have a smaller conflict surface;
- two PIF-based mods may still conflict if they modify the same small part of the same object, but they should not need to conflict because of the entire object.

PIF should generally be loaded before mods that are built on top of it. Mods that directly overwrite the same vanilla objects may still conflict regardless of load order.

## Using PIF in other mods

PIF provides two main mechanisms for modders.

### Category inline scripts

Each object is split into semantic categories.

For example, a building may have separate inline scripts for:

```txt
availability
economy
lifecycle
jobs
economic_modifiers
planet_state
ai
```

A job may have separate inline scripts for:

```txt
availability
economy
pop_config
swap
planet_state
country_modifiers
pop_modifiers
economic_modifiers
```

A mod can overwrite only the needed inline script instead of copying the full object.

### Scripted variables

Meaningful parameters are moved into variables.

For example:

- cost;
- upkeep;
- production;
- number of jobs;
- job weights;
- promotion/demotion time;
- planet/country/pop modifiers;
- important top-level flags for jobs.

This allows balance changes to be made through variables without overwriting the objects themselves.

## Documentation

Detailed technical documentation is available in `docs/`.

Recommended entry points:

- [Affected vanilla files and objects](docs/AFFECTED_VANILLA_FILES.md);
- [Districts layer specification](docs/districts_EN.md);
- [Zones layer specification](docs/zones_EN.md);
- [Zone slots layer specification](docs/zone_slots_EN.md);
- [Buildings layer specification](docs/buildings_EN.md);
- [Jobs layer specification](docs/jobs_EN.md);
- [Build, analysis, generation, and validation tools](docs/PIF_TOOLS_REFERENCE_EN.md).

Russian documentation is also available in corresponding `_RU.md` files.

## Repository structure

The repository is organized around three main areas:

```txt
mod/
docs/
build-scripts/
```

`mod/` contains the generated game files.

`docs/` contains user-facing and technical documentation.

`build-scripts/` contains the analysis, generation, and validation tooling used to build the framework from vanilla data.

## Stellaris version

PIF is built from the vanilla Stellaris **4.3.7** files.

The descriptor uses:

```txt
4.3.*
```

The intended compatibility range is the Stellaris 4.3 branch, while the actual baseline used for generation is **4.3.7**.

## Feedback

I would appreciate reports about bugs, compatibility problems, or any case where PIF unexpectedly changes vanilla behavior.

Especially useful reports include:

- errors related to PIF files;
- examples of conflicts with other mods;
- cases where an object behaves differently than in vanilla;
- suggestions for improving the inline script or variable structure.

PIF was created as a practical tool for modders, so feedback from real use is especially valuable.
