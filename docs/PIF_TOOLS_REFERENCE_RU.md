# PIF tooling — техническая документация

## Оглавление

- [Назначение документа](#назначение-документа)
- [Назначение tooling](#назначение-tooling)
- [Общая модель pipeline](#общая-модель-pipeline)
  - [Profile](#profile)
  - [Backend](#backend)
  - [Category inline scripts](#category-inline-scripts)
  - [Variable domains](#variable-domains)
  - [Static validation](#static-validation)
- [Структура build-scripts](#структура-build-scripts)
- [Поддерживаемые профили](#поддерживаемые-профили)
- [Входные данные](#входные-данные)
- [Выходные данные](#выходные-данные)
- [Command reference](#command-reference)
  - [`pif_analyze.py`](#pif_analyzepy)
  - [`pif_split_inline_scripts.py`](#pif_split_inline_scriptspy)
  - [`pif_generate_layer.py`](#pif_generate_layerpy)
  - [`pif_validate_layer.py`](#pif_validate_layerpy)
  - [`pif_run_all.py`](#pif_run_allpy)
- [Быстрый запуск](#быстрый-запуск)
- [Правила работы с inline scripts](#правила-работы-с-inline-scripts)
- [Правила работы с scripted variables](#правила-работы-с-scripted-variables)
- [Правила порядка и сравнения AST](#правила-порядка-и-сравнения-ast)
- [Профильные особенности](#профильные-особенности)
  - [`districts`](#districts)
  - [`zones`](#zones)
  - [`zone_slots`](#zone_slots)
  - [`buildings`](#buildings)
  - [`jobs`](#jobs)
- [Контрольные показатели pipeline](#контрольные-показатели-pipeline)
- [Reports и manifests](#reports-и-manifests)
- [Как добавлять новый профиль](#как-добавлять-новый-профиль)
- [Как обновлять правила под изменившийся vanilla baseline](#как-обновлять-правила-под-изменившийся-vanilla-baseline)
- [Troubleshooting](#troubleshooting)

## Назначение документа

Этот документ описывает текущее устройство скриптов генерации, анализа и валидации Planetary Infrastructure Framework.

Его задача — зафиксировать, как пользоваться `build-scripts`, какие профили поддерживаются, какие файлы создаются, какие проверки выполняются и какие технические решения заложены в pipeline. Документ описывает рабочее поведение скриптов, а не историю их разработки.

## Назначение tooling

Tooling PIF нужен для воспроизводимого построения framework layer из vanilla baseline. Скрипты не принимают балансных решений и не “улучшают” vanilla-объекты вручную. Их задача — механически перенести vanilla-поведение в PIF-архитектуру и проверить, что expanded PIF остаётся эквивалентен expanded vanilla с учётом явно разрешённых нормализаций.

Pipeline решает пять задач:

1. Загружает vanilla baseline из `Planet.zip` или распакованной папки.
2. Рекурсивно раскрывает `inline_script`.
3. Анализирует фактические параметры объектов после expansion.
4. Генерирует normalized PIF layer: один object-file на vanilla object, category inline scripts и scripted variables.
5. Выполняет static validation generated layer против vanilla baseline.

## Общая модель pipeline

### Profile

`Profile` описывает семейство объектов, с которым работают общие CLI-скрипты. Профили зарегистрированы в `pif_profiles.py`.

Профиль задаёт:

- имя CLI-профиля;
- исходную vanilla folder;
- output folder внутри generated layer;
- object label;
- object prefix, если он применим;
- список canonical categories;
- функцию классификации параметров;
- функцию statement-level нормализации;
- backend генерации;
- backend валидации;
- имя generation manifest;
- имя validation report.

Поддерживаемые профили:

```txt
buildings
districts
jobs
zone_slots
zones
```

### Backend

`Backend` — профиль-специфичный модуль в `pif_backends/`. Общие CLI-команды одинаковы для всех профилей, но backend содержит правила конкретного типа объектов.

Backend нужен потому, что разные объектные слои имеют разную структуру:

- `districts` делятся на real districts и district masks;
- `zones` имеют building compatibility и `swap_type`;
- `zone_slots` почти не имеют gameplay-логики, но являются структурным контейнером zones;
- `buildings` требуют semantic split modifier-carrier blocks;
- `jobs` требуют отдельной обработки job flags, `resources`, `overlord_resources`, weights и modifier blocks.

### Category inline scripts

Category inline script — PIF-owned файл, содержащий одну смысловую часть объекта.

Пример:

```txt
common/inline_scripts/pif/buildings/building_research_lab_1/economy.txt
common/inline_scripts/pif/jobs/researcher/weight.txt
common/inline_scripts/pif/zones/zone_research/availability.txt
```

Category scripts уменьшают зону конфликтов между модами. Мод, меняющий только экономику объекта, не должен переписывать весь object-file.

### Variable domains

Variable domain — смысловая категория значений в `common/scripted_variables`.

Variable domain не обязан совпадать с object category. Object category отвечает на вопрос “где эта часть объекта находится”, а variable domain отвечает на вопрос “что это значение контролирует”. Например, `base_buildtime` может оставаться в root object, но переменная для него относится к construction domain.

Общие правила:

- vanilla `@variables` resolve-ятся в конкретные значения;
- PIF variables создаются object-specific;
- aliases вида `@pif_x = @pif_y` не создаются;
- `value:` expressions не превращаются в PIF variables;
- nested trigger booleans обычно остаются literal;
- top-level job boolean flags являются исключением и выносятся в job flag variables.

### Static validation

Static validation сравнивает expanded vanilla object и expanded generated PIF object.

Validator раскрывает PIF category inline scripts, resolve-ит generated PIF variables, применяет разрешённые profile normalizations и сравнивает canonical representation. Это structural equivalence check; он не заменяет проверку в игре.

## Структура build-scripts

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

| Файл | Назначение |
|---|---|
| `pif_stellaris.py` | Parser, renderer, loader, inline expansion, shared AST helpers. |
| `pif_profiles.py` | Реестр профилей и dispatch-настройки. |
| `pif_analyze.py` | Анализ vanilla objects выбранного профиля. |
| `pif_split_inline_scripts.py` | Анализ reachable vanilla inline scripts и необходимость распила. |
| `pif_generate_layer.py` | Генерация PIF layer для выбранного профиля. |
| `pif_validate_layer.py` | Static validation generated layer. |
| `pif_run_all.py` | Полный pipeline одной командой. |
| `pif_backends/*` | Профильная генерация, классификация, переменные и validation. |

## Поддерживаемые профили

| Profile | Vanilla source folder | Generated folder | Object label | Backend modules |
|---|---|---|---|---|
| `districts` | `common/districts` | `common/districts` | district | `districts_generate.py`, `districts_validate.py` |
| `zones` | `common/zones` | `common/zones` | zone | `zones_generate.py`, `zones_validate.py` |
| `zone_slots` | `common/zone_slots` | `common/zone_slots` | zone slot | `zone_slots_generate.py`, `zone_slots_validate.py` |
| `buildings` | `common/buildings` | `common/buildings` | building | `buildings_common.py`, `buildings_generate.py`, `buildings_validate.py` |
| `jobs` | `common/pop_jobs` | `common/pop_jobs` | job | `jobs_common.py`, `jobs_generate.py`, `jobs_validate.py` |

## Входные данные

Скрипты принимают vanilla baseline двумя способами:

```txt
--planet /path/to/Planet.zip
--planet /path/to/extracted/Planet
```

`Planet.zip` распаковывается во временную директорию. Если используется zip, можно указать `--work-dir`, чтобы контролировать место распаковки.

Ожидается, что baseline содержит нужные vanilla folders и зависимые `inline_scripts` / `scripted_variables`. Если baseline неполный, анализ или validation могут дать missing inline script, missing object или unresolved variable.

## Выходные данные

Pipeline создаёт два типа результатов:

1. Runtime layer — generated PIF files, которые могут быть помещены в мод.
2. Reports — CSV/JSON отчёты для анализа и проверки.

Типовая generated структура:

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

Reports пишутся отдельно, обычно в `<reports>/<profile>/`:

```txt
analysis/
inline_scripts/
<profile>_run_all_summary.json
```

## Command reference

Все команды поддерживают общие аргументы:

| Аргумент | Обязателен | Назначение |
|---|---|---|
| `--profile` | да, кроме helper-вызовов из кода | Один из `districts`, `zones`, `zone_slots`, `buildings`, `jobs`. |
| `--planet` | нет, но практически нужен | Путь к `Planet.zip` или распакованному baseline. |
| `--work-dir` | нет | Папка для распаковки zip. |

### `pif_analyze.py`

Анализирует vanilla objects выбранного профиля после recursive inline expansion.

```bash
python pif_analyze.py \
  --profile buildings \
  --planet /path/to/Planet.zip \
  --out /path/to/reports/buildings/analysis
```

Выходы:

| Файл | Содержимое |
|---|---|
| `<profile>_objects.csv` | Object key, class, source file, source stem, top-level params after expansion. |
| `<profile>_parameters_after_expansion.csv` | Использование параметров после expansion, включая class breakdown. |
| `<profile>_reachable_inline_scripts.csv` | Reachable inline scripts, object count, call count, objects. |
| `<profile>_analysis_summary.json` | Summary анализа. |

### `pif_split_inline_scripts.py`

Анализирует reachable vanilla inline scripts выбранного профиля.

```bash
python pif_split_inline_scripts.py \
  --profile jobs \
  --planet /path/to/Planet.zip \
  --out /path/to/reports/jobs/inline_scripts
```

Скрипт классифицирует each reachable inline script как:

| Decision | Значение |
|---|---|
| `WHOLE` | Script после expansion относится к одной category или к metadata-only fragment. |
| `SPLIT` | Script смешивает разные category owners и должен быть разложен по PIF categories. |

Для `buildings` и `jobs` classification использует profile-specific semantic split helpers, потому что modifier-carrier blocks классифицируются по содержимому.

Выходы:

| Файл | Содержимое |
|---|---|
| `<profile>_inline_scripts_summary.csv` | Inline script, decision, categories, parameters, counters. |
| `<profile>_inline_direct_calls.csv` | Direct inline calls из root object bodies. |
| `<profile>_inline_nested_edges.csv` | Nested inline script edges. |
| `<profile>_inline_script_split_summary.json` | Summary по reachable/whole/split. |

### `pif_generate_layer.py`

Генерирует PIF layer выбранного профиля.

```bash
python pif_generate_layer.py \
  --profile zones \
  --planet /path/to/Planet.zip \
  --out /path/to/generated/zones \
  --clean
```

Аргументы:

| Аргумент | Назначение |
|---|---|
| `--out` | Generated PIF root. Если не задан, используется default output профиля. |
| `--clean` | Удалить output directory перед генерацией. |
| `--sparse-empty` | Для профилей, которые поддерживают режим, пропускать пустые category scripts. |

`--sparse-empty` поддерживается profile dispatch для `zones`, `buildings` и `jobs`. Для `districts` и `zone_slots` пустые extension hooks являются частью спецификации и не пропускаются.

### `pif_validate_layer.py`

Проверяет generated layer против vanilla baseline.

```bash
python pif_validate_layer.py \
  --profile buildings \
  --planet /path/to/Planet.zip \
  --generated /path/to/generated/buildings \
  --out /path/to/generated/buildings/pif_building_validation_report.json
```

Аргументы:

| Аргумент | Назначение |
|---|---|
| `--generated` | Generated PIF root. |
| `--out` | Путь к JSON validation report. Если не задан, используется profile report name внутри generated root. |

Validator возвращает summary с `checked`, `ok`, `failed`, `warnings` если backend их формирует, и path к report.

### `pif_run_all.py`

Запускает полный pipeline:

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

`pif_run_all.py` пишет итоговый summary:

```txt
<reports>/<profile>/<profile>_run_all_summary.json
```

## Быстрый запуск

Пример полного прогона для всех профилей:

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

Для сборки единого runtime-мода обычно удобнее генерировать профили в один общий output root, если backend layout не конфликтует:

```bash
python pif_run_all.py --profile districts  --planet /path/to/Planet.zip --out /path/to/PIF --reports /path/to/reports --clean
python pif_run_all.py --profile zones      --planet /path/to/Planet.zip --out /path/to/PIF --reports /path/to/reports
python pif_run_all.py --profile zone_slots --planet /path/to/Planet.zip --out /path/to/PIF --reports /path/to/reports
python pif_run_all.py --profile buildings  --planet /path/to/Planet.zip --out /path/to/PIF --reports /path/to/reports
python pif_run_all.py --profile jobs       --planet /path/to/Planet.zip --out /path/to/PIF --reports /path/to/reports
```

В этом варианте `--clean` используется только на первом профиле, иначе следующий профиль удалит output предыдущего.

## Правила работы с inline scripts

Vanilla inline scripts используются как source material. Они раскрываются, анализируются и преобразуются в PIF-owned category inline scripts.

Классификация `WHOLE` не означает обязательное сохранение runtime-ссылки на vanilla script. Она означает, что script после expansion относится к одной category и может быть перенесён как единый смысловой блок. Классификация `SPLIT` означает, что script смешивает несколько category owners и должен быть разложен.

Для `buildings` и `jobs` statement category не всегда определяется top-level key. Modifier-carrier параметры вроде `triggered_planet_modifier` классифицируются по содержимому блока. Если один modifier block смешивает несколько смысловых групп, он не дробится построчно и остаётся в fallback `TPM`.

## Правила работы с scripted variables

Скрипты создают PIF variables только по правилам конкретного профиля.

Общие правила:

- variables группируются по domain file;
- внутри файла variables группируются по object key;
- vanilla `@variables` resolve-ятся в конкретные значения;
- generated PIF variables не ссылаются на другие PIF variables;
- `value:` scripted value expressions остаются как expressions;
- localization-selector constants не становятся variables;
- structural identity values обычно остаются literal;
- nested trigger booleans не выносятся в variables;
- top-level job boolean flags выносятся в `pif_jobs_flags_variables.txt`.

## Правила порядка и сравнения AST

Parser и renderer сохраняют порядок statement’ов. Это важно, потому что часть vanilla-структур order-sensitive.

Правила:

- `inline_script` раскрывается в месте подключения;
- repeated `triggered_*` blocks не сортируются;
- списки `convert_to`, `upgrades`, `zone_slots`, building filters и job `weight` сохраняют порядок;
- validation не использует безусловную alphabetic sorting там, где порядок может менять поведение;
- canonical comparison применяется только после profile-specific normalizations.

## Профильные особенности

### `districts`

Слой `districts` различает real districts и district masks.

Real districts генерируются по полной схеме:

```txt
METADATA + ZONE_SLOTS + AVAILABILITY + ECONOMIC + TPM + LIFECYCLE + AI
```

District masks остаются компактными:

```txt
METADATA + MASK
```

Особенности:

- `planet_modifier` нормализуется в `triggered_planet_modifier`;
- masks не получают functional hooks для economy, lifecycle или AI;
- localization selectors не становятся variables;
- variable layer содержит domain-specific district variables.

### `zones`

Слой `zones` связывает district/zone infrastructure, building compatibility и visual district masks.

Схема:

```txt
METADATA + AVAILABILITY + ZONE_CONFIG + ECONOMY + TPM + LIFECYCLE + AI
```

Особенности:

- `swap_type` и `swap_type_weight` остаются в root metadata;
- `zone_sets`, `include`, `excluded_building_sets` и related filters относятся к `ZONE_CONFIG`;
- static modifiers нормализуются в triggered equivalents;
- variables группируются по смысловым доменам, включая job-family domains.

### `zone_slots`

Слой `zone_slots` является структурным контейнером допустимых zones.

Схема:

```txt
METADATA + ZS_CONFIG + AVAILABILITY
```

Особенности:

- `start` остаётся в root object;
- `include`, `exclude`, `included_zone_sets`, `excluded_zone_sets` идут в `ZS_CONFIG`;
- `potential` и `unlock` идут в `AVAILABILITY`;
- vanilla zone slots не используют inline scripts;
- variables не создаются.

### `buildings`

Слой `buildings` загружает все top-level objects из `common/buildings`, а не только keys с префиксом `building_`.

Object classes:

```txt
regular
capital
branch
holding
special
```

Особенности:

- branch office buildings и holdings имеют отдельную структуру;
- non-`building_` objects сохраняются;
- modifier carriers классифицируются по содержимому;
- mixed modifier blocks остаются в `TPM`;
- meaningful numeric tuning values выносятся в object-specific building variables;
- boolean flags не становятся building variables.

### `jobs`

Слой `jobs` загружает все top-level objects из `common/pop_jobs`, включая jobs без `category`.

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

Особенности:

- `resources` и `overlord_resources` относятся к job economy;
- `weight`, `promotion`, `demotion`, `swappable_data`, `possible_precalc` и `auto_trait_prio` имеют профильные правила;
- modifier carriers классифицируются по содержимому;
- `planet_modifier` и `country_modifier` нормализуются в triggered equivalents;
- top-level boolean job flags намеренно выносятся в variables;
- nested boolean logic внутри triggers остаётся literal.

## Контрольные показатели pipeline

Контрольные показатели нужны для smoke-check после изменения скриптов или baseline. Если числа меняются, это не всегда ошибка, но изменение должно быть объяснено изменением входных данных или profile rules.

| Profile | Objects | Reachable inline scripts | WHOLE | SPLIT | Category scripts | Variables | Variable files | Validation |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `districts` | 138 | 47 | 45 | 2 | 348 | 553 | 10 | 138 / 138 OK |
| `zones` | 120 | 39 | 19 | 20 | 720 | 1553 | 14 | 120 / 120 OK |
| `zone_slots` | 27 | 0 | 0 | 0 | 54 | 0 | 0 | 27 / 27 OK |
| `buildings` | 490 | 54 | 42 | 12 | 5390 | 5881 | 12 | 490 / 490 OK |
| `jobs` | 373 | 27 | 17 | 10 | 3357 | 2682 | 12 | 373 / 373 OK |

## Reports и manifests

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

Generation manifest пишется в generated root и фиксирует созданные object files, category scripts, variables и предупреждения backend-а.

Типовые имена:

```txt
pif_district_generation_manifest.json
pif_zone_generation_manifest.json
pif_zone_slot_generation_manifest.json
pif_building_generation_manifest.json
pif_job_generation_manifest.json
```

### Validation reports

Validation report пишется в generated root, если `--out` не задан отдельно.

Типовые имена:

```txt
pif_district_validation_report.json
pif_zone_validation_report.json
pif_zone_slot_validation_report.json
pif_building_validation_report.json
pif_job_validation_report.json
```

## Как добавлять новый профиль

Минимальный порядок:

1. Добавить loader object family в `pif_stellaris.py` или отдельный helper.
2. Описать categories и category display names.
3. Добавить profile entry в `pif_profiles.py`.
4. Добавить generation backend в `pif_backends/<profile>_generate.py`.
5. Добавить validation backend в `pif_backends/<profile>_validate.py`.
6. Если параметр classification зависит от содержимого блока, вынести common helpers в `pif_backends/<profile>_common.py`.
7. Прогнать `pif_analyze.py`.
8. Проверить inline scripts через `pif_split_inline_scripts.py`.
9. Реализовать generation и variable allocation.
10. Реализовать static validation.
11. Прогнать `pif_run_all.py`.

Новый профиль не должен требовать копирования CLI-скриптов. Общие команды должны продолжить работать через profile/backend dispatch.

## Как обновлять правила под изменившийся vanilla baseline

Порядок:

1. Заменить входной vanilla baseline.
2. Запустить `pif_analyze.py` для каждого профиля.
3. Сравнить новые параметры с текущей спецификацией.
4. Запустить `pif_split_inline_scripts.py` и проверить новые `SPLIT`/unknown cases.
5. Обновить category mapping, normalization и variable domains, если vanilla изменился.
6. Запустить generation.
7. Запустить validation.
8. Проверить runtime log в игре.

Если validation проходит, но runtime log показывает ошибки, сначала проверяются:

- порядок blocks;
- unresolved scripted variables;
- context-sensitive inline script placement;
- modifier normalization;
- mixed modifier blocks;
- `value:` expressions.

## Troubleshooting

| Симптом | Что проверить |
|---|---|
| `Unknown PIF profile` | Имя профиля должно быть одним из `districts`, `zones`, `zone_slots`, `buildings`, `jobs`. |
| `inline_script not found` | Baseline неполный или vanilla script path изменился. |
| `missing generated object` | Loader/generator не создал object или output root не тот. |
| `expanded body differs` | Ошибка category split, normalization, variable replacement или order-sensitive placement. |
| `Unknown variable` в игре | Проверить generated `common/scripted_variables` и references в category scripts. |
| `Object with key already exists` в игре | Для PIF это ожидаемый override-шум, если строка указывает на generated PIF object. |
| `SPLIT` scripts резко выросли | Проверить новые vanilla inline scripts и modifier-carrier classification. |
| Количество variables изменилось | Проверить variable domains, deduplication и новые scalar values в baseline. |
| Jobs не заполняются в игре | Проверить `possible_pre_triggers`, `possible_precalc`, `possible`, `weight`, top-level flags и сохранение порядка `weight` blocks. |
