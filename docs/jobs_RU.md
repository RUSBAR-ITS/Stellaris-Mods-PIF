# Jobs — техническая спецификация PIF

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

Этот документ описывает техническую организацию слоя `pop_jobs` в Planetary Infrastructure Framework. Он фиксирует, как PIF анализирует jobs, eligibility-логику, веса назначения pop-ов, экономику, swap-данные, automation flags, modifier blocks, переменные и проверки эквивалентности vanilla-поведению.

## Общая характеристика слоя

`pop_jobs` описывают, какую работу могут выполнять pops, кто может занимать job, с каким весом pop выбирает job, какие ресурсы job производит или потребляет, какие modifier effects он создаёт, и как job участвует в automation, promotion, demotion и swap logic.

Jobs отличаются от buildings тем, что top-level boolean flags часто являются самостоятельной настраиваемой логикой. Поэтому PIF выносит такие flags в variable layer, но не превращает в переменные все nested `yes/no` внутри trigger-блоков.

## Методика анализа

### Анализ параметров

Параметры анализируются после рекурсивной развёртки reachable `inline_script`. PIF смотрит на фактическую структуру объекта, а не на комментарии, предполагаемое назначение файла или имя переменной. Если параметр является modifier-carrier block, его категория может определяться содержимым блока, а не только именем параметра.

### Анализ переменных

Variable domains проектируются отдельно от parameter categories: они описывают, что значение контролирует в gameplay/balance, а не где оно расположено в AST. Для jobs top-level boolean flags считаются meaningful variables, потому что они управляют capped logic, automation, priority UI, AI availability и similar behavior. Vanilla `@variables` resolve-ятся в конкретные значения и заменяются PIF-specific variables, чтобы не сохранять старые глобальные точки конфликта. `value:` expressions и control-flow constants не превращаются в PIF variables.

### Анализ inline scripts

Все reachable vanilla inline scripts классифицируются после рекурсивного expansion. `WHOLE` означает, что script относится к одной PIF category. `SPLIT` означает, что script смешивает несколько categories и должен быть разложен по PIF-owned category scripts. Если один modifier block смешивает несколько смыслов, он не дробится построчно и переносится в fallback category.

## Классы объектов

Классы объектов нужны для выбора корректной PIF schema. Они не используются для изменения gameplay; они описывают, какие structural hooks безопасны для данного вида объекта.

| Класс | Объектов | Назначение |
| --- | --- | --- |
| ruler | 14 | Jobs категории `ruler`. |
| specialist | 102 | Jobs категории `specialist`. |
| worker | 52 | Jobs категории `worker`. |
| complex_drone | 80 | Gestalt jobs категории `complex_drone`. |
| simple_drone | 32 | Gestalt jobs категории `simple_drone`. |
| special/other | 75 | Purge, pre-sapient, precursor, unemployment, criminal, slave, assimilation и другие специальные категории. |
| no category | 18 | Jobs без top-level `category`; это не считается ошибкой и сохраняется как отдельный класс анализа. |

## Архитектура PIF-слоя

### Файлы объектов

Каждый vanilla object переносится в отдельный normalized PIF object file:

```txt
common/pop_jobs/pif_<vanilla_file_stem>_<job_key>.txt
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
common/inline_scripts/pif/jobs/<job_key>/<category>.txt
```

Category script является минимальной conflict zone. Мод, который меняет только экономику объекта, не должен переписывать availability, lifecycle или AI того же объекта.

### Порядок категорий

Порядок подключения category scripts фиксирован и является частью PIF schema:

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

Порядок нужен для воспроизводимой генерации, читаемости и корректной static validation. Он не должен изменяться случайной сортировкой.

## Категории параметров

Категории параметров определяют, в какой PIF-owned inline script помещается конкретная часть объекта. Категория параметров не обязана совпадать с доменом переменной. Modifier-carrier parameters классифицируются по содержимому блока; сам `triggered_planet_modifier` не считается самостоятельной category.

| Категория | Где находится | Зачем нужна | Параметры |
| --- | --- | --- | --- |
| METADATA | Root object | Identity fields that define what the job is. | `category`, `purge`. |
| SWAP | Inline script | Job swap data. | `swappable_data`. |
| AVAILABILITY | Inline script | Eligibility and cap logic for whether a pop may fill the job. | `possible_pre_triggers`, `possible_precalc`, `possible`, `is_capped_by_modifier`. |
| POP_CONFIG | Inline script | Assignment, tags, automation, promotion/demotion and top-level job flags. | `weight`, `tags`, `promotion`, `demotion`, `auto_trait_prio`, top-level flags. |
| ECONOMY | Inline script | Normal and overlord-directed job economy. | `resources`, `overlord_resources`. |
| PLANET_STATE | Inline script | Clean planet-state modifier blocks. | Amenities, crime, stability, defense armies. |
| COUNTRY_MODIFIERS | Inline script | Clean country-level modifier blocks. | Naval cap, edict fund, leader and country effects. |
| POP_MODIFIERS | Inline script | Clean pop-level modifier blocks. | Happiness, growth, assembly, workforce, pop-group modifiers. |
| ECONOMIC_MODIFIERS | Inline script | Clean output/upkeep modifier blocks outside `resources`. | Job output and upkeep modifier keys. |
| TPM | Inline script | Fallback for mixed, system, rare and special modifier blocks. | Mixed modifier carriers and rare effects. |

## Категории переменных

| Domain file | Variables | Назначение |
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

Итого: **12** файлов переменных и **2682** переменных.

## Inline scripts

### Политика работы с inline scripts

Vanilla inline scripts используются как source material для построения PIF-owned category scripts. Решение `WHOLE` означает, что expanded script относится к одной категории. Решение `SPLIT` означает, что expanded script должен быть разложен по категориям. Для этого слоя найдено **27** reachable inline scripts: **17** `WHOLE`, **10** `SPLIT`.

### Достижимые inline scripts

| Inline script | Решение | Категории | Параметры |
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

### Правила распила

- `WHOLE` script переносится или разворачивается как единый смысловой блок внутри соответствующей PIF category.
- `SPLIT` script разворачивается и распределяется по категориям.
- Script с пустым содержимым может использоваться как no-op source material, но не создаёт gameplay content.
- PIF-owned category scripts являются итоговым слоем совместимости.
- Если один modifier block смешивает несколько смысловых групп, он не дробится построчно и помещается в `TPM` fallback.

## Нормализации

| Нормализация | Зачем нужна | Требование к проверке |
| --- | --- | --- |
| `planet_modifier` -> `triggered_planet_modifier` | Позволяет расширять modifier blocks независимо. | Unconditional trigger должен быть эквивалентен static vanilla modifier. |
| `country_modifier` -> `triggered_country_modifier` | Позволяет расширять country-scope modifier blocks независимо. | Expanded result должен сохранять vanilla semantics. |
| Vanilla `@variable` -> PIF variable | Создаёт object-specific tuning points вместо сохранения общих vanilla variables. | Resolved PIF value должен совпадать с исходным значением. |
| Inline script expansion and split | Уменьшает conflict zones за счёт переноса содержимого в PIF-owned category scripts. | Expanded PIF object должен совпадать с expanded vanilla object после разрешённых нормализаций. |

## Порядок параметров

Категория определяет владение параметром, но не отменяет порядок. Генератор и validator должны сохранять order-sensitive sections. Repeated blocks нельзя сортировать автоматически, если порядок может влиять на выбор первого valid target, отображение tooltip или итоговое применение effects.

Особенно важны `weight`, `promotion`, `demotion`, repeated modifier blocks, `auto_trait_prio` и порядок category inline calls.

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

Текущий результат: **373 / 373 OK**, failed: **0**.

## Runtime-проверка

Static validation подтверждает структурную эквивалентность, но runtime smoke test всё равно нужен: движок может зависеть от контекста, который не виден при AST-сравнении.

Минимальная runtime-проверка должна включать запуск новой игры, открытие планетарного UI, проверку обычной империи, hive, machine, corporate контекста, habitats/ringworld/ecumenopolis при возможности, а также просмотр `error.log` на ошибки, связанные с `pif_` files.

## Статистика слоя

| Метрика | Значение |
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

## Статистика параметров

| Параметр | Тип | Всего | Ruler | Specialist | Worker | Complex drone | Simple drone | Special/other | No category | Назначение | Категория | Действие |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `is_capped_by_modifier` | modifier / flag | 173 | 3 | 32 | 30 | 20 | 18 | 70 | 0 | Указывает, что количество jobs задаётся modifier-ами вида `job_<key>_add`. | AVAILABILITY | Вынести в PIF-owned inline script соответствующей категории. |
| `possible` | trigger block | 328 | 13 | 79 | 42 | 72 | 30 | 74 | 18 | Основное условие, может ли pop занимать job. | AVAILABILITY | Вынести в PIF-owned inline script соответствующей категории. |
| `possible_pre_triggers` | trigger block | 302 | 8 | 84 | 45 | 62 | 29 | 74 | 0 | Быстрые предварительные фильтры перед `possible`. | AVAILABILITY | Вынести в PIF-owned inline script соответствующей категории. |
| `possible_precalc` | atom / enum | 216 | 7 | 69 | 30 | 62 | 27 | 21 | 0 | Предрасчитанный eligibility-фильтр job-а. | AVAILABILITY | Вынести в PIF-owned inline script соответствующей категории. |
| `overlord_resources` | resources block | 61 | 0 | 19 | 13 | 17 | 9 | 3 | 0 | Экономический блок job-а, направленный overlord-стороне в subject/overlord context. | ECONOMY | Вынести в PIF-owned inline script соответствующей категории. |
| `resources` | resources block | 267 | 8 | 78 | 39 | 61 | 24 | 57 | 0 | Экономический блок: cost, upkeep, produces и economic category. | ECONOMY | Вынести в PIF-owned inline script соответствующей категории. |
| `category` | atom / enum | 355 | 14 | 102 | 52 | 80 | 32 | 75 | 0 | Категория объекта в vanilla-системе. | METADATA | Оставить в корневом объекте. |
| `purge` | atom / enum | 4 | 0 | 0 | 0 | 0 | 0 | 4 | 0 | Тип purge logic для job. | METADATA | Оставить в корневом объекте. |
| `allow_only_same_rank_pops` | yes/no | 6 | 0 | 0 | 0 | 0 | 0 | 6 | 0 | Разрешает job только pop-ам того же rank/stratum. | POP_CONFIG | Вынести в PIF-owned inline script соответствующей категории. |
| `auto_generate_description` | yes/no | 2 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | Управляет автогенерацией описания эффектов. | POP_CONFIG | Вынести в PIF-owned inline script соответствующей категории. |
| `auto_trait_prio` | block / value | 126 | 4 | 47 | 21 | 34 | 15 | 5 | 0 | Приоритеты auto-modding traits для job-а. | POP_CONFIG | Вынести в PIF-owned inline script соответствующей категории. |
| `can_be_automated` | yes/no | 10 | 1 | 4 | 1 | 2 | 0 | 2 | 0 | Может ли job участвовать в automation. | POP_CONFIG | Вынести в PIF-owned inline script соответствующей категории. |
| `can_set_priority` | yes/no | 51 | 0 | 13 | 7 | 13 | 6 | 12 | 0 | Можно ли вручную менять приоритет job-а. | POP_CONFIG | Вынести в PIF-owned inline script соответствующей категории. |
| `contributes_to_diplo_weight` | yes/no | 24 | 0 | 0 | 0 | 0 | 0 | 24 | 0 | Участвует ли job в расчётах diplomatic weight. | POP_CONFIG | Вынести в PIF-owned inline script соответствующей категории. |
| `count_as_available_for_ai` | yes/no | 11 | 0 | 0 | 1 | 0 | 0 | 10 | 0 | Считать ли job доступным для AI. | POP_CONFIG | Вынести в PIF-owned inline script соответствующей категории. |
| `demotion` | block / value | 36 | 0 | 0 | 0 | 0 | 0 | 36 | 0 | Правила demotion из job/stratum. | POP_CONFIG | Вынести в PIF-owned inline script соответствующей категории. |
| `exempt_from_ai_amenity_prioritization` | yes/no | 3 | 0 | 2 | 1 | 0 | 0 | 0 | 0 | Исключение из AI amenity prioritization. | POP_CONFIG | Вынести в PIF-owned inline script соответствующей категории. |
| `first_come_first_served` | yes/no | 27 | 0 | 0 | 2 | 0 | 0 | 25 | 0 | Занятие job-а по принципу first come first served. | POP_CONFIG | Вынести в PIF-owned inline script соответствующей категории. |
| `ignores_sapience` | yes/no | 13 | 0 | 0 | 0 | 0 | 0 | 13 | 0 | Игнорирует ли job sapience pop-а. | POP_CONFIG | Вынести в PIF-owned inline script соответствующей категории. |
| `promotion` | block / value | 208 | 8 | 78 | 35 | 56 | 27 | 4 | 0 | Правила promotion в job/stratum. | POP_CONFIG | Вынести в PIF-owned inline script соответствующей категории. |
| `tags` | list / block | 251 | 8 | 75 | 41 | 55 | 26 | 46 | 0 | Теги job-а для AI, automation, scripted checks и группировки. | POP_CONFIG | Вынести в PIF-owned inline script соответствующей категории. |
| `triggered_tags` | block / value | 2 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | Условные теги job-а. | POP_CONFIG | Вынести в PIF-owned inline script соответствующей категории. |
| `weight` | block / value | 290 | 7 | 81 | 45 | 59 | 29 | 69 | 0 | Вес назначения pop-а на job. | POP_CONFIG | Вынести в PIF-owned inline script соответствующей категории. |
| `swappable_data` | block / value | 352 | 14 | 102 | 49 | 80 | 32 | 59 | 16 | Данные для job swap logic. | SWAP | Вынести в PIF-owned inline script соответствующей категории. |
| `country_modifier` | modifier / flag | 12 | 1 | 7 | 0 | 4 | 0 | 0 | 0 | Статический country modifier carrier. | content-based modifier category | Классифицировать block по содержимому; static modifier при необходимости нормализовать. |
| `planet_modifier` | modifier / flag | 52 | 1 | 17 | 9 | 12 | 3 | 10 | 0 | Статический planet modifier carrier. | content-based modifier category | Классифицировать block по содержимому; static modifier при необходимости нормализовать. |
| `system_modifier` | modifier / flag | 2 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | System-level modifier carrier. | content-based modifier category | Классифицировать block по содержимому; static modifier при необходимости нормализовать. |
| `triggered_country_modifier` | modifier / flag | 48 | 1 | 23 | 4 | 17 | 2 | 1 | 0 | Условный country modifier carrier. | content-based modifier category | Классифицировать block по содержимому; static modifier при необходимости нормализовать. |
| `triggered_planet_modifier` | modifier / flag | 123 | 8 | 38 | 18 | 20 | 9 | 30 | 0 | Условный planet modifier carrier. | content-based modifier category | Классифицировать block по содержимому; static modifier при необходимости нормализовать. |
| `triggered_planet_pop_group_modifier_for_all` | modifier / flag | 2 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | Условный modifier для всех pop groups планеты. | content-based modifier category | Классифицировать block по содержимому; static modifier при необходимости нормализовать. |
| `triggered_planet_pop_group_modifier_for_species` | modifier / flag | 6 | 0 | 2 | 0 | 4 | 0 | 0 | 0 | Условный modifier для pop groups конкретного species. | content-based modifier category | Классифицировать block по содержимому; static modifier при необходимости нормализовать. |

## Особые случаи и технические предупреждения

- Jobs без `category` сохраняются как отдельный класс анализа.
- `possible_precalc` нельзя выводить автоматически из `category`; оно копируется из vanilla как есть.
- `auto_trait_prio` относится к auto-modding species trait selection, а не к job assignment weight.
- `overlord_resources` является economy block, направленным на overlord-сторону.
- Top-level boolean flags являются variables; nested trigger booleans остаются literal.

## Затронутые vanilla-объекты

Этот раздел перечисляет vanilla objects, которые переопределяются PIF для данного слоя.

### `pop_jobs/00_other_jobs.txt`

| Object | Класс | PIF file |
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

| Object | Класс | PIF file |
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

| Object | Класс | PIF file |
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

| Object | Класс | PIF file |
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

| Object | Класс | PIF file |
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

| Object | Класс | PIF file |
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

| Object | Класс | PIF file |
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

| Object | Класс | PIF file |
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

| Object | Класс | PIF file |
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

| Object | Класс | PIF file |
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

| Object | Класс | PIF file |
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

| Object | Класс | PIF file |
| --- | --- | --- |
| `munitions_decommissioner` | `specialist` | `common/pop_jobs/pif_11_astral_planes_jobs_munitions_decommissioner.txt` |
| `munitions_decommissioning_unit` | `complex_drone` | `common/pop_jobs/pif_11_astral_planes_jobs_munitions_decommissioning_unit.txt` |
| `munitions_decommissioning_unit_lithoid` | `complex_drone` | `common/pop_jobs/pif_11_astral_planes_jobs_munitions_decommissioning_unit_lithoid.txt` |
| `munitions_decommissioning_drone` | `complex_drone` | `common/pop_jobs/pif_11_astral_planes_jobs_munitions_decommissioning_drone.txt` |
| `astral_researcher` | `specialist` | `common/pop_jobs/pif_11_astral_planes_jobs_astral_researcher.txt` |
| `astral_drone` | `complex_drone` | `common/pop_jobs/pif_11_astral_planes_jobs_astral_drone.txt` |
| `astral_unit` | `complex_drone` | `common/pop_jobs/pif_11_astral_planes_jobs_astral_unit.txt` |

### `pop_jobs/12_cosmic_storm_jobs.txt`

| Object | Класс | PIF file |
| --- | --- | --- |
| `astrometeorologist` | `specialist` | `common/pop_jobs/pif_12_cosmic_storm_jobs_astrometeorologist.txt` |
| `astrometeorologist_hive` | `complex_drone` | `common/pop_jobs/pif_12_cosmic_storm_jobs_astrometeorologist_hive.txt` |
| `astrometeorologist_machine` | `complex_drone` | `common/pop_jobs/pif_12_cosmic_storm_jobs_astrometeorologist_machine.txt` |

### `pop_jobs/13_machine_age_jobs.txt`

| Object | Класс | PIF file |
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

| Object | Класс | PIF file |
| --- | --- | --- |
| `treasure_gatherer` | `specialist` | `common/pop_jobs/pif_14_grand_archive_jobs_treasure_gatherer.txt` |
| `wrangler` | `specialist` | `common/pop_jobs/pif_14_grand_archive_jobs_wrangler.txt` |
| `drone_wrangler` | `complex_drone` | `common/pop_jobs/pif_14_grand_archive_jobs_drone_wrangler.txt` |
| `treasure_gatherer_gestalt` | `complex_drone` | `common/pop_jobs/pif_14_grand_archive_jobs_treasure_gatherer_gestalt.txt` |

### `pop_jobs/15_biogenesis_jobs.txt`

| Object | Класс | PIF file |
| --- | --- | --- |
| `disconnected_drone` | `simple_drone` | `common/pop_jobs/pif_15_biogenesis_jobs_disconnected_drone.txt` |
| `skywatcher` | `specialist` | `common/pop_jobs/pif_15_biogenesis_jobs_skywatcher.txt` |
| `skywatcher_drone` | `complex_drone` | `common/pop_jobs/pif_15_biogenesis_jobs_skywatcher_drone.txt` |
| `genomic_researcher` | `specialist` | `common/pop_jobs/pif_15_biogenesis_jobs_genomic_researcher.txt` |
| `genomic_drone` | `complex_drone` | `common/pop_jobs/pif_15_biogenesis_jobs_genomic_drone.txt` |
| `transference_volunteer` | `specialist` | `common/pop_jobs/pif_15_biogenesis_jobs_transference_volunteer.txt` |
| `transference_drone` | `complex_drone` | `common/pop_jobs/pif_15_biogenesis_jobs_transference_drone.txt` |

### `pop_jobs/15_gestalt_unemployment.txt`

| Object | Класс | PIF file |
| --- | --- | --- |
| `complex_drone_unemployment` | `special_other` | `common/pop_jobs/pif_15_gestalt_unemployment_complex_drone_unemployment.txt` |
| `simple_drone_unemployment` | `special_other` | `common/pop_jobs/pif_15_gestalt_unemployment_simple_drone_unemployment.txt` |

### `pop_jobs/15_strange_worlds_jobs.txt`

| Object | Класс | PIF file |
| --- | --- | --- |
| `sand_whisperer` | `specialist` | `common/pop_jobs/pif_15_strange_worlds_jobs_sand_whisperer.txt` |
| `sand_caretaker` | `specialist` | `common/pop_jobs/pif_15_strange_worlds_jobs_sand_caretaker.txt` |
| `drone_sand_whisperer` | `complex_drone` | `common/pop_jobs/pif_15_strange_worlds_jobs_drone_sand_whisperer.txt` |
| `drone_sand_caretaker` | `complex_drone` | `common/pop_jobs/pif_15_strange_worlds_jobs_drone_sand_caretaker.txt` |
| `space_junk_collector` | `specialist` | `common/pop_jobs/pif_15_strange_worlds_jobs_space_junk_collector.txt` |
| `drone_space_junk_collector` | `complex_drone` | `common/pop_jobs/pif_15_strange_worlds_jobs_drone_space_junk_collector.txt` |

### `pop_jobs/15_unemployment.txt`

| Object | Класс | PIF file |
| --- | --- | --- |
| `ruler_unemployment` | `special_other` | `common/pop_jobs/pif_15_unemployment_ruler_unemployment.txt` |
| `specialist_unemployment` | `special_other` | `common/pop_jobs/pif_15_unemployment_specialist_unemployment.txt` |
| `worker_unemployment` | `special_other` | `common/pop_jobs/pif_15_unemployment_worker_unemployment.txt` |
| `bio_trophy_unemployment` | `special_other` | `common/pop_jobs/pif_15_unemployment_bio_trophy_unemployment.txt` |
| `slave_unemployment` | `special_other` | `common/pop_jobs/pif_15_unemployment_slave_unemployment.txt` |

### `pop_jobs/16_shroud_jobs.txt`

| Object | Класс | PIF file |
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

| Object | Класс | PIF file |
| --- | --- | --- |
| `duelist` | `specialist` | `common/pop_jobs/pif_99_swap_jobs_duelist.txt` |
| `historical_curator` | `specialist` | `common/pop_jobs/pif_99_swap_jobs_historical_curator.txt` |
| `storm_dancer` | `specialist` | `common/pop_jobs/pif_99_swap_jobs_storm_dancer.txt` |

## Использованные исходные файлы и документация

| Type | Files |
| --- | --- |
| Vanilla object files | `common/pop_jobs/*.txt` |
| Inline scripts | reachable files under `common/inline_scripts/` |
| Scripted variables | `common/scripted_variables/*.txt` |
| Object documentation | `common/pop_jobs/000_pretriggers.txt` and actual `common/pop_jobs` objects |
| Generated reports | `Analytics/reports/jobs/` |
