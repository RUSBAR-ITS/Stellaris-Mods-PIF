# Zone Slots — техническая спецификация PIF

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

Этот документ описывает техническую организацию слоя `zone_slots` в Planetary Infrastructure Framework. Он фиксирует, как PIF анализирует слоты зон, сохраняет их структурную роль внутри районов, выделяет категории конфигурации и доступности, формирует PIF-owned inline scripts и проверяет сохранение vanilla-поведения.

## Общая характеристика слоя

`zone_slots` описывают, какие zones могут находиться внутри района. Это самый компактный слой планетарной инфраструктуры, но он критичен для сохранения структуры district layout.

Слой почти не содержит числового баланса и не использует reachable vanilla inline scripts. Поэтому PIF сохраняет его как лёгкую object-per-file схему с двумя categories: конфигурация слота и availability.

## Методика анализа

### Анализ параметров

Параметры анализируются после рекурсивной развёртки reachable `inline_script`. PIF смотрит на фактическую структуру объекта, а не на комментарии, предполагаемое назначение файла или имя переменной. Если параметр является modifier-carrier block, его категория может определяться содержимым блока, а не только именем параметра.

### Анализ переменных

Для этого слоя meaningful variables не выделяются, но отсутствие переменных является результатом анализа, а не предположением. Vanilla `@variables` resolve-ятся в конкретные значения и заменяются PIF-specific variables, чтобы не сохранять старые глобальные точки конфликта. `value:` expressions и control-flow constants не превращаются в PIF variables.

### Анализ inline scripts

Все reachable vanilla inline scripts классифицируются после рекурсивного expansion. `WHOLE` означает, что script относится к одной PIF category. `SPLIT` означает, что script смешивает несколько categories и должен быть разложен по PIF-owned category scripts. Если один modifier block смешивает несколько смыслов, он не дробится построчно и переносится в fallback category.

## Классы объектов

Классы объектов нужны для выбора корректной PIF schema. Они не используются для изменения gameplay; они описывают, какие structural hooks безопасны для данного вида объекта.

| Класс | Объектов | Назначение |
| --- | --- | --- |
| zone slot | 27 | Основной и единственный класс объектов. Все slots получают одинаковую PIF-схему. |

## Архитектура PIF-слоя

### Файлы объектов

Каждый vanilla object переносится в отдельный normalized PIF object file:

```txt
common/zone_slots/pif_<vanilla_file_stem>_<zone_slot_key>.txt
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
common/inline_scripts/pif/zone_slots/<zone_slot_key>/<category>.txt
```

Category script является минимальной conflict zone. Мод, который меняет только экономику объекта, не должен переписывать availability, lifecycle или AI того же объекта.

### Порядок категорий

Порядок подключения category scripts фиксирован и является частью PIF schema:

```txt
zs_config
availability
```

Порядок нужен для воспроизводимой генерации, читаемости и корректной static validation. Он не должен изменяться случайной сортировкой.

## Категории параметров

Категории параметров определяют, в какой PIF-owned inline script помещается конкретная часть объекта. Категория параметров не обязана совпадать с доменом переменной.

| Категория | Где находится | Зачем нужна | Параметры |
| --- | --- | --- | --- |
| METADATA | Root object | Core slot metadata. | `start`. |
| ZS_CONFIG | Inline script | Фильтры и наборы зон, допустимые для слота. | `include`, `exclude`, `included_zone_sets`, `excluded_zone_sets`. |
| AVAILABILITY | Inline script | Условия существования и разблокировки слота. | `potential`, `unlock`. |

## Категории переменных

Для этого слоя не выделены значимые variable domains. Vanilla-объекты не содержат meaningful tuning scalars, которые требуют выноса в PIF scripted variables.

## Inline scripts

### Политика работы с inline scripts

Vanilla inline scripts используются как source material для построения PIF-owned category scripts. Решение `WHOLE` означает, что expanded script относится к одной категории. Решение `SPLIT` означает, что expanded script должен быть разложен по категориям. Для этого слоя найдено **0** reachable inline scripts: **0** `WHOLE`, **0** `SPLIT`.

### Достижимые inline scripts

Reachable vanilla inline scripts не найдены.

### Правила распила

- `WHOLE` script переносится или разворачивается как единый смысловой блок внутри соответствующей PIF category.
- `SPLIT` script разворачивается и распределяется по категориям.
- Script с пустым содержимым может использоваться как no-op source material, но не создаёт gameplay content.
- PIF-owned category scripts являются итоговым слоем совместимости.

## Нормализации

| Нормализация | Зачем нужна | Требование к проверке |
| --- | --- | --- |
| Inline script policy | Этот слой не использует reachable vanilla inline scripts. | Generated PIF scripts являются structural extension points. |

## Порядок параметров

Категория определяет владение параметром, но не отменяет порядок. Генератор и validator должны сохранять order-sensitive sections. Repeated blocks нельзя сортировать автоматически, если порядок может влиять на выбор первого valid target, отображение tooltip или итоговое применение effects.

Особенно важны `start`, порядок include/exclude filters и сохранение служебных slots.

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

Текущий результат: **27 / 27 OK**, failed: **0**.

## Runtime-проверка

Static validation подтверждает структурную эквивалентность, но runtime smoke test всё равно нужен: движок может зависеть от контекста, который не виден при AST-сравнении.

Минимальная runtime-проверка должна включать запуск новой игры, открытие планетарного UI, проверку обычной империи, hive, machine, corporate контекста, habitats/ringworld/ecumenopolis при возможности, а также просмотр `error.log` на ошибки, связанные с `pif_` files.

## Статистика слоя

| Метрика | Значение |
| --- | --- |
| Objects | 27 |
| Source files | 2 |
| Parameter names after expansion | 6 |
| Category inline scripts | 54 |
| Variable files | 0 |
| PIF variables | 0 |
| Reachable inline scripts | 0 |
| Inline scripts WHOLE | 0 |
| Inline scripts SPLIT | 0 |
| Validation checked | 27 |
| Validation OK | 27 |
| Validation failed | 0 |

## Статистика параметров

| Параметр | Объектов | Категория | Действие |
| --- | --- | --- | --- |
| `potential` | 3 | AVAILABILITY | Вынести в отдельный inline script категории. |
| `unlock` | 27 | AVAILABILITY | Вынести в отдельный inline script категории. |
| `start` | 2 | METADATA | Оставить в корневом объекте. |
| `exclude` | 1 | ZS_CONFIG | Вынести в отдельный inline script категории. |
| `include` | 1 | ZS_CONFIG | Вынести в отдельный inline script категории. |
| `included_zone_sets` | 26 | ZS_CONFIG | Вынести в отдельный inline script категории. |

## Особые случаи и технические предупреждения

- `slot_city_05` сохраняется даже если не используется текущими districts.
- `slot_empty` сохраняется как служебный slot для district masks.
- Особенность `slot_city_government` и `zone_default` не исправляется автоматически, потому что PIF сохраняет vanilla-поведение.

## Затронутые vanilla-объекты

Этот раздел перечисляет vanilla objects, которые переопределяются PIF для данного слоя.

### `zone_slots/00_zone_slots.txt`

| Object | Класс | PIF file |
| --- | --- | --- |
| `slot_city_government` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_city_government.txt` |
| `slot_city_01` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_city_01.txt` |
| `slot_city_02` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_city_02.txt` |
| `slot_minerals` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_minerals.txt` |
| `slot_energy` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_energy.txt` |
| `slot_food` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_food.txt` |
| `slot_city_04` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_city_04.txt` |
| `slot_city_05` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_city_05.txt` |
| `slot_rw_urban_01` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_rw_urban_01.txt` |
| `slot_rw_urban_02` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_rw_urban_02.txt` |
| `slot_rw_urban_03` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_rw_urban_03.txt` |
| `slot_arcology_urban_01` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_arcology_urban_01.txt` |
| `slot_arcology_urban_02` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_arcology_urban_02.txt` |
| `slot_arcology_urban_03` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_arcology_urban_03.txt` |
| `slot_nexus` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_nexus.txt` |
| `slot_hive` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_hive.txt` |
| `slot_cosmogenesis_government` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_cosmogenesis_government.txt` |
| `slot_empty` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_empty.txt` |
| `slot_resort_01` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_resort_01.txt` |
| `slot_resort_02` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_resort_02.txt` |
| `slot_resort_attraction_01` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_resort_attraction_01.txt` |
| `slot_polytechnic` | `zone_slot` | `common/zone_slots/pif_00_zone_slots_slot_polytechnic.txt` |

### `zone_slots/01_habitat_zone_slots.txt`

| Object | Класс | PIF file |
| --- | --- | --- |
| `slot_habitat_01` | `zone_slot` | `common/zone_slots/pif_01_habitat_zone_slots_slot_habitat_01.txt` |
| `slot_habitat_02` | `zone_slot` | `common/zone_slots/pif_01_habitat_zone_slots_slot_habitat_02.txt` |
| `slot_habitat_energy` | `zone_slot` | `common/zone_slots/pif_01_habitat_zone_slots_slot_habitat_energy.txt` |
| `slot_habitat_minerals` | `zone_slot` | `common/zone_slots/pif_01_habitat_zone_slots_slot_habitat_minerals.txt` |
| `slot_habitat_research` | `zone_slot` | `common/zone_slots/pif_01_habitat_zone_slots_slot_habitat_research.txt` |

## Использованные исходные файлы и документация

| Type | Files |
| --- | --- |
| Vanilla object files | `common/zone_slots/*.txt` |
| Inline scripts | reachable files under `common/inline_scripts/` |
| Scripted variables | `common/scripted_variables/*.txt` |
| Object documentation | `common/zone_slots/99_HOW_TO_ZONE.txt` |
| Generated reports | `Analytics/reports/zone_slots/` |
