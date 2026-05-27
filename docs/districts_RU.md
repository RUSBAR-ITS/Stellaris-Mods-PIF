# Districts — техническая спецификация PIF

## Оглавление

- [Назначение документа](#назначение-документа)
- [Общая характеристика слоя](#общая-характеристика-слоя)
- [Методика анализа](#методика-анализа)
  - [Анализ параметров](#анализ-параметров)
  - [Анализ переменных](#анализ-переменных)
  - [Анализ inline scripts](#анализ-inline-scripts)
- [Классы объектов](#классы-объектов)
- [Архитектура PIF-слоя](#архитектура-pif-слоя)
  - [Файлы объектов](#файлы-объектов)
  - [Корневой объект](#корневой-объект)
  - [Скрипты категорий](#скрипты-категорий)
  - [Порядок категорий](#порядок-категорий)
- [Категории параметров](#категории-параметров)
- [Категории переменных](#категории-переменных)
- [Inline Scripts](#inline-scripts)
  - [Политика работы с inline scripts](#политика-работы-с-inline-scripts)
  - [Достижимые inline scripts](#достижимые-inline-scripts)
  - [Правила распила](#правила-распила)
- [Нормализации](#нормализации)
- [Порядок параметров](#порядок-параметров)
- [Статическая проверка](#статическая-проверка)
- [Runtime-проверка](#runtime-проверка)
- [Статистика слоя](#статистика-слоя)
- [Статистика параметров](#статистика-параметров)
- [Особые случаи и технические предупреждения](#особые-случаи-и-технические-предупреждения)
- [Затронутые vanilla-объекты](#затронутые-vanilla-объекты)
- [Использованные исходные файлы и документация](#использованные-исходные-файлы-и-документация)

## Назначение документа

Этот документ описывает техническую организацию слоя `districts` в Planetary Infrastructure Framework. Он фиксирует, как PIF анализирует vanilla-районы, отделяет настоящие районы от визуальных масок, раскладывает параметры по категориям, формирует PIF-owned inline scripts, создаёт доменные переменные и проверяет сохранение vanilla-поведения.

## Общая характеристика слоя

`districts` задают базовую планетарную структуру. В PIF этот слой важен не только как набор строимых районов, но и как набор визуальных масок, используемых zones через `swap_type`.

Главное техническое различие внутри слоя — разделение на настоящие районы и district masks. Настоящие районы получают полную PIF-схему: структура zone slots, availability, economy, modifiers, lifecycle и AI. Маски не получают функциональные hooks, потому что их задача — визуальное отображение выбранного типа зоны, а не создание строимого объекта.

## Методика анализа

### Анализ параметров

Параметры анализируются после рекурсивной развёртки reachable `inline_script`. PIF смотрит на фактическую структуру объекта, а не на комментарии, предполагаемое назначение файла или имя переменной. Если параметр является modifier-carrier block, его категория может определяться содержимым блока, а не только именем параметра.

### Анализ переменных

Variable domains проектируются отдельно от parameter categories: они описывают, что значение контролирует в gameplay/balance, а не где оно расположено в AST. Vanilla `@variables` resolve-ятся в конкретные значения и заменяются PIF-specific variables, чтобы не сохранять старые глобальные точки конфликта. `value:` expressions и control-flow constants не превращаются в PIF variables.

### Анализ inline scripts

Все reachable vanilla inline scripts классифицируются после рекурсивного expansion. `WHOLE` означает, что script относится к одной PIF category. `SPLIT` означает, что script смешивает несколько categories и должен быть разложен по PIF-owned category scripts. Если один modifier block смешивает несколько смыслов, он не дробится построчно и переносится в fallback category.

## Классы объектов

Классы объектов нужны для выбора корректной PIF schema. Они не используются для изменения gameplay; они описывают, какие structural hooks безопасны для данного вида объекта.

| Класс | Объектов | Назначение |
| --- | --- | --- |
| real district | 58 | Функциональный район с полной PIF-схемой. |
| active district mask | 77 | Визуальная маска, на которую есть ссылка из `zone.swap_type`. |
| sleeping district mask | 3 | Визуальная маска с масочной структурой без активной ссылки из текущих zones. |

## Архитектура PIF-слоя

### Файлы объектов

Каждый vanilla object переносится в отдельный normalized PIF object file:

```txt
common/districts/pif_<vanilla_file_stem>_<district_key>.txt
```

Правила:

- один top-level object на файл;
- имя файла сохраняет источник через `vanilla_file_stem`;
- object key включается в имя файла, чтобы путь был однозначным;
- root object содержит metadata и `inline_script` calls к PIF-owned category scripts.

### Корневой объект

Корневой объект содержит параметры, которые должны оставаться рядом с object identity, UI или engine-sensitive структурой. Эти поля не выносятся в отдельный category script, если отдельный hook не даёт практической совместимости или может создать ложную точку расширения.

В корневом объекте также размещаются calls к PIF-owned inline scripts в фиксированном порядке категорий.

### Скрипты категорий

Каждая функциональная категория размещается в собственном PIF-owned inline script:

```txt
common/inline_scripts/pif/districts/<district_key>/<category>.txt
```

Category script является минимальной conflict zone. Мод, который меняет только экономику объекта, не должен переписывать availability, lifecycle или AI того же объекта.

### Порядок категорий

Порядок подключения category scripts фиксирован и является частью PIF schema:

```txt
zone_slots
availability
economic
tpm
lifecycle
ai
```

Порядок нужен для воспроизводимой генерации, читаемости и корректной static validation. Он не должен изменяться случайной сортировкой.

## Категории параметров

Категории параметров определяют, в какой PIF-owned inline script помещается конкретная часть объекта. Категория параметров не обязана совпадать с доменом переменной.

| Категория | Где находится | Зачем нужна | Параметры |
| --- | --- | --- | --- |
| METADATA | Root object | Engine/UI/core-поля, identity и поля, для которых отдельный hook создаёт больше шума, чем пользы. | `base_buildtime`, `icon`, `overlay_icon`, planner flags, localization blocks. |
| ZONE_SLOTS | Inline script | Структурный layout района. | `zone_slots`. |
| AVAILABILITY | Inline script | Условия существования, постройки и разблокировки района. | `potential`, `allow`, `prerequisites`. |
| ECONOMIC | Inline script | Экономика района как объекта. | `resources`. |
| TPM | Inline script | Planet/pop-group modifiers, jobs and housing modifiers. | `planet_modifier`, `triggered_planet_modifier`. |
| LIFECYCLE | Inline script | События и конверсии района. | `destroy_trigger`, `on_*`, `convert_to`, `conversion_ratio`. |
| AI | Inline script | AI-планирование districts. | `ai_resource_production`, `additional_ai_weight`, `ai_weight_coefficient`. |
| MASK | Root object for masks | Visual layer district masks. | `gridbox`, `triggered_name`, `triggered_flavor_desc`, icons. |

## Категории переменных

| Domain file | Variables | Назначение |
| --- | --- | --- |
| `pif_districts_ai_variables.txt` | 63 | Числа AI-планирования districts. |
| `pif_districts_building_capacity_variables.txt` | 2 | Дополнительная building capacity от districts. |
| `pif_districts_construction_variables.txt` | 125 | Цена строительства и время строительства districts. |
| `pif_districts_conversion_variables.txt` | 41 | Conversion ratios для `convert_to`. |
| `pif_districts_defense_variables.txt` | 1 | Оборонительные эффекты district. |
| `pif_districts_economy_variables.txt` | 77 | Содержание и прямое производство districts. |
| `pif_districts_housing_variables.txt` | 117 | Housing capacity от districts. |
| `pif_districts_infrastructure_effects_variables.txt` | 8 | Infrastructure effects вроде скорости строительства и enact speed. |
| `pif_districts_jobs_variables.txt` | 103 | Количество jobs, добавляемых district modifiers. |
| `pif_districts_limits_variables.txt` | 16 | Deposit-based district limits. |

Итого: **10** файлов переменных и **553** переменных.

## Inline scripts

### Политика работы с inline scripts

Vanilla inline scripts используются как source material для построения PIF-owned category scripts. Решение `WHOLE` означает, что expanded script относится к одной категории. Решение `SPLIT` означает, что expanded script должен быть разложен по категориям. Для этого слоя найдено **47** reachable inline scripts: **45** `WHOLE`, **2** `SPLIT`.

### Достижимые inline scripts

| Inline script | Решение | Категории | Параметры |
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

### Правила распила

- `WHOLE` script переносится или разворачивается как единый смысловой блок внутри соответствующей PIF category.
- `SPLIT` script разворачивается и распределяется по категориям.
- Script с пустым содержимым может использоваться как no-op source material, но не создаёт gameplay content.
- PIF-owned category scripts являются итоговым слоем совместимости.

## Нормализации

| Нормализация | Зачем нужна | Требование к проверке |
| --- | --- | --- |
| `planet_modifier` -> `triggered_planet_modifier` | Позволяет расширять modifier blocks независимо. | Unconditional trigger должен быть эквивалентен static vanilla modifier. |
| Vanilla `@variable` -> PIF variable | Создаёт object-specific tuning points вместо сохранения общих vanilla variables. | Resolved PIF value должен совпадать с исходным значением. |
| Inline script expansion and split | Уменьшает conflict zones за счёт переноса содержимого в PIF-owned category scripts. | Expanded PIF object должен совпадать с expanded vanilla object после разрешённых нормализаций. |

## Порядок параметров

Категория определяет владение параметром, но не отменяет порядок. Генератор и validator должны сохранять order-sensitive sections. Repeated blocks нельзя сортировать автоматически, если порядок может влиять на выбор первого valid target, отображение tooltip или итоговое применение effects.

Особенно важны порядок `zone_slots`, `convert_to`, repeated `triggered_*` blocks и visual metadata district masks.

## Статическая проверка

Validation сравнивает expanded vanilla objects с expanded PIF objects после применения явно разрешённых нормализаций.

Проверяются:

- наличие всех expected objects;
- отсутствие лишних generated objects;
- resolved inline scripts;
- resolved PIF variables;
- отсутствие duplicate или missing variables;
- совпадение expanded category content;
- сохранение order-sensitive sections;
- warning-level special cases без превращения vanilla-особенностей в hard failure.

Текущий результат: **138 / 138 OK**, failed: **0**.

## Runtime-проверка

Static validation подтверждает структурную эквивалентность, но runtime smoke test всё равно нужен: движок может зависеть от контекста, который не виден при AST-сравнении.

Минимальная runtime-проверка должна включать запуск новой игры, открытие планетарного UI, проверку обычной империи, hive, machine, corporate контекста, habitats/ringworld/ecumenopolis при возможности, а также просмотр `error.log` на ошибки, связанные с `pif_` files.

## Статистика слоя

| Метрика | Значение |
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

## Статистика параметров

| Параметр | SUM | Real | Active mask | Sleeping mask | Категория | Действие |
| --- | --- | --- | --- | --- | --- | --- |
| `additional_ai_weight` | 7 | 7 | 0 | 0 | AI | Вынести в PIF-owned inline script соответствующей категории. |
| `ai_estimate_without_unemployment` | 6 | 6 | 0 | 0 | AI | Вынести в PIF-owned inline script соответствующей категории. |
| `ai_resource_production` | 8 | 8 | 0 | 0 | AI | Вынести в PIF-owned inline script соответствующей категории. |
| `ai_weight_coefficient` | 8 | 8 | 0 | 0 | AI | Вынести в PIF-owned inline script соответствующей категории. |
| `exempt_from_ai_planet_specialization` | 30 | 30 | 0 | 0 | AI | Вынести в PIF-owned inline script соответствующей категории. |
| `allow` | 27 | 27 | 0 | 0 | AVAILABILITY | Вынести в PIF-owned inline script соответствующей категории. |
| `potential` | 138 | 58 | 77 | 3 | class-dependent | Для real objects вынести по схеме; для masks сохранить как guard/visual metadata. |
| `prerequisites` | 13 | 13 | 0 | 0 | AVAILABILITY | Вынести в PIF-owned inline script соответствующей категории. |
| `resources` | 51 | 51 | 0 | 0 | ECONOMIC | Вынести в PIF-owned inline script соответствующей категории. |
| `conversion_ratio` | 41 | 41 | 0 | 0 | LIFECYCLE | Вынести в PIF-owned inline script соответствующей категории. |
| `convert_to` | 45 | 45 | 0 | 0 | LIFECYCLE | Вынести в PIF-owned inline script соответствующей категории. |
| `destroy_trigger` | 1 | 1 | 0 | 0 | LIFECYCLE | Вынести в PIF-owned inline script соответствующей категории. |
| `on_built` | 3 | 3 | 0 | 0 | LIFECYCLE | Вынести в PIF-owned inline script соответствующей категории. |
| `on_queued` | 4 | 4 | 0 | 0 | LIFECYCLE | Вынести в PIF-owned inline script соответствующей категории. |
| `on_unqueued` | 4 | 4 | 0 | 0 | LIFECYCLE | Вынести в PIF-owned inline script соответствующей категории. |
| `base_buildtime` | 56 | 56 | 0 | 0 | METADATA | Оставить в корневом объекте. |
| `can_demolish` | 1 | 1 | 0 | 0 | METADATA | Оставить в корневом объекте. |
| `default_starting_district` | 1 | 1 | 0 | 0 | METADATA | Оставить в корневом объекте. |
| `desc` | 1 | 1 | 0 | 0 | METADATA | Оставить в корневом объекте. |
| `expansion_planner` | 12 | 12 | 0 | 0 | METADATA | Оставить в корневом объекте. |
| `expansion_planner_type` | 5 | 5 | 0 | 0 | METADATA | Оставить в корневом объекте. |
| `gridbox` | 25 | 0 | 22 | 3 | METADATA | Оставить в корневом объекте. |
| `icon` | 92 | 25 | 64 | 3 | class-dependent | Для real objects вынести по схеме; для masks сохранить как guard/visual metadata. |
| `inherits_capped_modifiers_from` | 4 | 4 | 0 | 0 | METADATA | Оставить в корневом объекте. |
| `is_uncapped` | 13 | 13 | 0 | 0 | METADATA | Оставить в корневом объекте. |
| `max_for_deposits_on_planet` | 8 | 8 | 0 | 0 | METADATA | Оставить в корневом объекте. |
| `min_for_deposits_on_planet` | 8 | 8 | 0 | 0 | METADATA | Оставить в корневом объекте. |
| `overlay_icon` | 132 | 53 | 76 | 3 | class-dependent | Для real objects вынести по схеме; для masks сохранить как guard/visual metadata. |
| `show_on_uncolonized` | 138 | 58 | 77 | 3 | class-dependent | Для real objects вынести по схеме; для masks сохранить как guard/visual metadata. |
| `triggered_desc` | 11 | 11 | 0 | 0 | METADATA | Оставить в корневом объекте. |
| `triggered_flavor_desc` | 36 | 12 | 21 | 3 | class-dependent | Для real objects вынести по схеме; для masks сохранить как guard/visual metadata. |
| `triggered_name` | 106 | 28 | 75 | 3 | class-dependent | Для real objects вынести по схеме; для masks сохранить как guard/visual metadata. |
| `planet_modifier` | 46 | 46 | 0 | 0 | TPM | Нормализовать в triggered equivalent и затем классифицировать. |
| `triggered_planet_modifier` | 51 | 51 | 0 | 0 | TPM | Вынести в PIF-owned inline script соответствующей категории. |
| `zone_slots` | 138 | 58 | 77 | 3 | class-dependent | Для real objects вынести по схеме; для masks сохранить как guard/visual metadata. |

## Особые случаи и технические предупреждения

- District masks не получают функциональные hooks для economy, lifecycle или AI.
- Active mask определяется через фактические `zone.swap_type` references.
- Localization-selection scalars вроде `num_zones value > 0` остаются literal.

## Затронутые vanilla-объекты

Этот раздел перечисляет vanilla objects, которые переопределяются PIF для данного слоя.

### `districts/00_special_districts.txt`

| Object | Класс | PIF file |
| --- | --- | --- |
| `district_cosmogenesis_goverment` | `real` | `common/districts/pif_00_special_districts_district_cosmogenesis_goverment.txt` |
| `district_cosmogenesis_world_science` | `real` | `common/districts/pif_00_special_districts_district_cosmogenesis_world_science.txt` |
| `district_cosmogenesis_world_logic` | `real` | `common/districts/pif_00_special_districts_district_cosmogenesis_world_logic.txt` |
| `district_mindlink` | `real` | `common/districts/pif_00_special_districts_district_mindlink.txt` |

### `districts/00_urban_districts.txt`

| Object | Класс | PIF file |
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

| Object | Класс | PIF file |
| --- | --- | --- |
| `district_arcology_housing` | `real` | `common/districts/pif_01_arcology_districts_district_arcology_housing.txt` |
| `district_arcology_leisure` | `real` | `common/districts/pif_01_arcology_districts_district_arcology_leisure.txt` |
| `district_arcology_urban_1` | `real` | `common/districts/pif_01_arcology_districts_district_arcology_urban_1.txt` |
| `district_arcology_urban_2` | `real` | `common/districts/pif_01_arcology_districts_district_arcology_urban_2.txt` |
| `district_arcology_urban_3` | `real` | `common/districts/pif_01_arcology_districts_district_arcology_urban_3.txt` |

### `districts/02_rural_districts.txt`

| Object | Класс | PIF file |
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

| Object | Класс | PIF file |
| --- | --- | --- |
| `district_hab_housing` | `real` | `common/districts/pif_03_habitat_districts_district_hab_housing.txt` |
| `district_hab_energy` | `real` | `common/districts/pif_03_habitat_districts_district_hab_energy.txt` |
| `district_hab_mining` | `real` | `common/districts/pif_03_habitat_districts_district_hab_mining.txt` |
| `district_hab_science` | `real` | `common/districts/pif_03_habitat_districts_district_hab_science.txt` |

### `districts/04_ringworld_districts.txt`

| Object | Класс | PIF file |
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

| Object | Класс | PIF file |
| --- | --- | --- |
| `district_craglands` | `real` | `common/districts/pif_05_wilderness_districts_district_craglands.txt` |
| `district_photosynthesis_fields` | `real` | `common/districts/pif_05_wilderness_districts_district_photosynthesis_fields.txt` |
| `district_photosynthesis_fields_uncapped` | `real` | `common/districts/pif_05_wilderness_districts_district_photosynthesis_fields_uncapped.txt` |
| `district_hollow_mountains` | `real` | `common/districts/pif_05_wilderness_districts_district_hollow_mountains.txt` |
| `district_hollow_mountains_uncapped` | `real` | `common/districts/pif_05_wilderness_districts_district_hollow_mountains_uncapped.txt` |
| `district_orchard_forests` | `real` | `common/districts/pif_05_wilderness_districts_district_orchard_forests.txt` |
| `district_orchard_forests_uncapped` | `real` | `common/districts/pif_05_wilderness_districts_district_orchard_forests_uncapped.txt` |

### `districts/06_swap_districts.txt`

| Object | Класс | PIF file |
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

## Использованные исходные файлы и документация

| Type | Files |
| --- | --- |
| Vanilla object files | `common/districts/*.txt` |
| Inline scripts | reachable files under `common/inline_scripts/` |
| Scripted variables | `common/scripted_variables/*.txt` |
| Object documentation | `common/districts/00_DOCUMENTATION.txt` |
| Generated reports | `Analytics/reports/districts/` |
