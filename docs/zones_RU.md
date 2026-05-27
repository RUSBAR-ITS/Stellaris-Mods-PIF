# Zones — техническая спецификация PIF

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

Этот документ описывает техническую организацию слоя `zones` в Planetary Infrastructure Framework. Он фиксирует, как PIF анализирует зоны, сохраняет их роль связующего слоя между районами, слотами зон и зданиями, раскладывает параметры по категориям, формирует PIF-owned inline scripts, создаёт доменные переменные и проверяет сохранение vanilla-поведения.

## Общая характеристика слоя

`zones` являются связующим слоем планетарной инфраструктуры. Они определяют, какие building sets допускаются в конкретной зоне, какие zone sets назначены зоне, какие district masks используются для визуального swap-отображения, и какие планетарные/районные эффекты привязаны к зоне.

Для PIF этот слой особенно важен как compatibility boundary между районами и зданиями. Зоны нельзя рассматривать как простой список building filters: они участвуют в отображении, ограничениях, AI и conditional modifiers.

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
| zone | 120 | Основной и единственный класс объектов. Все zones получают одинаковую PIF-схему. |

## Архитектура PIF-слоя

### Файлы объектов

Каждый vanilla object переносится в отдельный normalized PIF object file:

```txt
common/zones/pif_<vanilla_file_stem>_<zone_key>.txt
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
common/inline_scripts/pif/zones/<zone_key>/<category>.txt
```

Category script является минимальной conflict zone. Мод, который меняет только экономику объекта, не должен переписывать availability, lifecycle или AI того же объекта.

### Порядок категорий

Порядок подключения category scripts фиксирован и является частью PIF schema:

```txt
availability
zone_config
economy
tpm
lifecycle
ai
```

Порядок нужен для воспроизводимой генерации, читаемости и корректной static validation. Он не должен изменяться случайной сортировкой.

## Категории параметров

Категории параметров определяют, в какой PIF-owned inline script помещается конкретная часть объекта. Категория параметров не обязана совпадать с доменом переменной.

| Категория | Где находится | Зачем нужна | Параметры |
| --- | --- | --- | --- |
| METADATA | Root object | Core/UI fields и swap metadata. | `icon`, `base_buildtime`, `swap_type`, `swap_type_weight`, capacity fields. |
| AVAILABILITY | Inline script | Условия существования, разблокировки и лимиты зоны. | `potential`, `unlock`, `planet_limit`. |
| ZONE_CONFIG | Inline script | Связь зоны с zone sets и building filters. | `zone_sets`, `include`, `included_building_sets`, `excluded_building_sets`. |
| ECONOMY | Inline script | Экономический блок зоны. | `resources`. |
| TPM | Inline script | Planet/district/country modifiers зоны. | `planet_modifier`, `triggered_district_planet_modifier`, etc. |
| LIFECYCLE | Inline script | Конверсии зоны. | `convert_to`. |
| AI | Inline script | AI-планирование зоны. | `ai_priority`, `ai_resource_production`, `ai_weight_coefficient`. |

## Категории переменных

| Domain file | Variables | Назначение |
| --- | --- | --- |
| `pif_zones_ai_variables.txt` | 171 | AI weights and resource hints for zones. |
| `pif_zones_building_capacity_variables.txt` | 129 | Building capacity, max buildings и slot capacity от zones. |
| `pif_zones_construction_variables.txt` | 236 | Время строительства и construction-related параметры zones. |
| `pif_zones_economy_variables.txt` | 0 | Reserved economy domain; no variables in current data. |
| `pif_zones_housing_variables.txt` | 96 | Housing effects от zone modifiers. |
| `pif_zones_jobs_defense_variables.txt` | 31 | Jobs и modifiers оборонительного назначения. |
| `pif_zones_jobs_industry_variables.txt` | 82 | Industrial job slots и производственные job modifiers. |
| `pif_zones_jobs_research_variables.txt` | 292 | Research job slots и research-related values. |
| `pif_zones_jobs_resource_extraction_variables.txt` | 158 | Resource extraction job slots. |
| `pif_zones_jobs_services_variables.txt` | 72 | Service and amenity job slots. |
| `pif_zones_jobs_trade_variables.txt` | 54 | Trade job slots. |
| `pif_zones_jobs_unity_admin_variables.txt` | 182 | Unity and administration job slots. |
| `pif_zones_limits_variables.txt` | 13 | Zone limits and cap-related values. |
| `pif_zones_planet_output_modifiers_variables.txt` | 37 | Planet output modifiers coming from zones. |

Итого: **14** файлов переменных и **1553** переменных.

## Inline scripts

### Политика работы с inline scripts

Vanilla inline scripts используются как source material для построения PIF-owned category scripts. Решение `WHOLE` означает, что expanded script относится к одной категории. Решение `SPLIT` означает, что expanded script должен быть разложен по категориям. Для этого слоя найдено **39** reachable inline scripts: **19** `WHOLE`, **20** `SPLIT`.

### Достижимые inline scripts

| Inline script | Решение | Категории | Параметры |
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

### Правила распила

- `WHOLE` script переносится или разворачивается как единый смысловой блок внутри соответствующей PIF category.
- `SPLIT` script разворачивается и распределяется по категориям.
- Script с пустым содержимым может использоваться как no-op source material, но не создаёт gameplay content.
- PIF-owned category scripts являются итоговым слоем совместимости.

## Нормализации

| Нормализация | Зачем нужна | Требование к проверке |
| --- | --- | --- |
| `planet_modifier` -> `triggered_planet_modifier` | Позволяет расширять modifier blocks независимо. | Unconditional trigger должен быть эквивалентен static vanilla modifier. |
| `country_modifier` -> `triggered_country_modifier` | Позволяет расширять country-scope modifier blocks независимо. | Expanded result должен сохранять vanilla semantics. |
| `district_planet_modifier` -> `triggered_district_planet_modifier` | Делает district-scoped zone modifiers расширяемыми. | Условие должно быть unconditional или эквивалентным. |
| Vanilla `@variable` -> PIF variable | Создаёт object-specific tuning points вместо сохранения общих vanilla variables. | Resolved PIF value должен совпадать с исходным значением. |
| Inline script expansion and split | Уменьшает conflict zones за счёт переноса содержимого в PIF-owned category scripts. | Expanded PIF object должен совпадать с expanded vanilla object после разрешённых нормализаций. |

## Порядок параметров

Категория определяет владение параметром, но не отменяет порядок. Генератор и validator должны сохранять order-sensitive sections. Repeated blocks нельзя сортировать автоматически, если порядок может влиять на выбор первого valid target, отображение tooltip или итоговое применение effects.

Особенно важны порядок `swap_type` / `swap_type_weight`, building filters, `convert_to` и repeated modifier blocks.

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

Текущий результат: **120 / 120 OK**, failed: **0**.

## Runtime-проверка

Static validation подтверждает структурную эквивалентность, но runtime smoke test всё равно нужен: движок может зависеть от контекста, который не виден при AST-сравнении.

Минимальная runtime-проверка должна включать запуск новой игры, открытие планетарного UI, проверку обычной империи, hive, machine, corporate контекста, habitats/ringworld/ecumenopolis при возможности, а также просмотр `error.log` на ошибки, связанные с `pif_` files.

## Статистика слоя

| Метрика | Значение |
| --- | --- |
| Objects | 120 |
| Source files | 5 |
| Parameter names after expansion | 22 |
| Category inline scripts | 720 |
| Variable files | 14 |
| PIF variables | 1553 |
| Reachable inline scripts | 39 |
| Inline scripts WHOLE | 19 |
| Inline scripts SPLIT | 20 |
| Validation checked | 120 |
| Validation OK | 120 |
| Validation failed | 0 |

## Статистика параметров

| Параметр | Объектов | Категория | Действие |
| --- | --- | --- | --- |
| `ai_priority` | 91 | AI | Вынести в PIF-owned inline script соответствующей категории. |
| `ai_resource_production` | 34 | AI | Вынести в PIF-owned inline script соответствующей категории. |
| `ai_weight_coefficient` | 25 | AI | Вынести в PIF-owned inline script соответствующей категории. |
| `planet_limit` | 13 | AVAILABILITY | Вынести в PIF-owned inline script соответствующей категории. |
| `potential` | 119 | AVAILABILITY | Вынести в PIF-owned inline script соответствующей категории. |
| `show_in_tech` | 10 | AVAILABILITY | Вынести в PIF-owned inline script соответствующей категории. |
| `unlock` | 119 | AVAILABILITY | Вынести в PIF-owned inline script соответствующей категории. |
| `resources` | 118 | ECONOMY | Вынести в PIF-owned inline script соответствующей категории. |
| `convert_to` | 41 | LIFECYCLE | Вынести в PIF-owned inline script соответствующей категории. |
| `base_buildtime` | 118 | METADATA | Оставить в корневом объекте. |
| `icon` | 119 | METADATA | Оставить в корневом объекте. |
| `max_buildings` | 17 | METADATA | Оставить в корневом объекте. |
| `max_buildings_planet_class` | 1 | METADATA | Оставить в корневом объекте. |
| `swap_type` | 77 | METADATA | Оставить в корневом объекте. |
| `swap_type_weight` | 77 | METADATA | Оставить в корневом объекте. |
| `triggered_desc` | 34 | METADATA | Оставить в корневом объекте. |
| `planet_modifier` | 112 | TPM | Нормализовать в triggered equivalent и затем классифицировать. |
| `triggered_district_planet_modifier` | 117 | TPM | Вынести в PIF-owned inline script соответствующей категории. |
| `excluded_building_sets` | 15 | ZONE_CONFIG | Вынести в PIF-owned inline script соответствующей категории. |
| `include` | 4 | ZONE_CONFIG | Вынести в PIF-owned inline script соответствующей категории. |
| `included_building_sets` | 117 | ZONE_CONFIG | Вынести в PIF-owned inline script соответствующей категории. |
| `zone_sets` | 120 | ZONE_CONFIG | Вынести в PIF-owned inline script соответствующей категории. |

## Особые случаи и технические предупреждения

- `swap_type` остаётся metadata, потому что он задаёт visual district mask и должен сохранять порядок рядом с `swap_type_weight`.
- `zone_sets` и building set filters являются совместимостью между zones и buildings, поэтому находятся в `ZONE_CONFIG`.
- Static modifiers нормализуются в triggered equivalents, когда это нужно для расширяемости.

## Затронутые vanilla-объекты

Этот раздел перечисляет vanilla objects, которые переопределяются PIF для данного слоя.

### `zones/00_zones.txt`

| Object | Класс | PIF file |
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

| Object | Класс | PIF file |
| --- | --- | --- |
| `zone_habitat_knights` | `zone` | `common/zones/pif_01_habitat_zones_zone_habitat_knights.txt` |
| `zone_habitat_hydroponics` | `zone` | `common/zones/pif_01_habitat_zones_zone_habitat_hydroponics.txt` |
| `zone_habitat_research` | `zone` | `common/zones/pif_01_habitat_zones_zone_habitat_research.txt` |
| `zone_habitat_research_unity` | `zone` | `common/zones/pif_01_habitat_zones_zone_habitat_research_unity.txt` |
| `zone_habitat_rare_crystals` | `zone` | `common/zones/pif_01_habitat_zones_zone_habitat_rare_crystals.txt` |
| `zone_habitat_volatile_motes` | `zone` | `common/zones/pif_01_habitat_zones_zone_habitat_volatile_motes.txt` |
| `zone_habitat_exotic_gases` | `zone` | `common/zones/pif_01_habitat_zones_zone_habitat_exotic_gases.txt` |

### `zones/02_special_zones.txt`

| Object | Класс | PIF file |
| --- | --- | --- |
| `zone_payback_enlightenment` | `zone` | `common/zones/pif_02_special_zones_zone_payback_enlightenment.txt` |
| `zone_broken_shackles_memorial` | `zone` | `common/zones/pif_02_special_zones_zone_broken_shackles_memorial.txt` |
| `zone_central_spire` | `zone` | `common/zones/pif_02_special_zones_zone_central_spire.txt` |

### `zones/03_wilderness_zones.txt`

| Object | Класс | PIF file |
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

| Object | Класс | PIF file |
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

## Использованные исходные файлы и документация

| Type | Files |
| --- | --- |
| Vanilla object files | `common/zones/*.txt` |
| Inline scripts | reachable files under `common/inline_scripts/` |
| Scripted variables | `common/scripted_variables/*.txt` |
| Object documentation | zone documentation files and actual `common/zones` objects |
| Generated reports | `Analytics/reports/zones/` |
