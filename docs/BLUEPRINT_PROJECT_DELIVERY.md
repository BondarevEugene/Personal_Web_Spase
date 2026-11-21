# Blueprint Studio · Полный пакет проектирования

Маршрут: `/demo/blueprint` → выбрать параметры → сформировать план → **Скачать пакет проекта (.zip)**.

В ZIP находятся:
- `SPECIFICATION.md` — предварительное ТЗ с критериями приёмки;
- `blueprint.json` — выбранные параметры и редакция;
- `architecture.json` — предложенные компоненты и зависимости, **не исполняемый Graph Studio workflow**;
- `milestones.json` — этапы, последовательность и ожидаемые результаты;
- `verification.json` — контрольные проверки, изначально `not_run`;
- `risks.json` — реестр рисков, изначально `open`;
- `acceptance.json` — критерии приёмки;
- `CHECKLIST.md` — действия до начала реализации;
- `manifest.json` — SHA-256 контрольные суммы каждого файла;
- `README.md` — описание ограничений пакета.

## Проверка целостности

```powershell
python -m scripts.verify_blueprint_package .\omnifactory-blueprint-REVISION.zip
python -m pytest -q tests/test_blueprint_project_plan_delivery.py
python -m ruff check omni_site/blueprint_project_plan.py omni_site/blueprint_delivery.py scripts/verify_blueprint_package.py tests/test_blueprint_project_plan_delivery.py
```

Проверяющий инструмент не распаковывает файлы на диск и не исполняет код из ZIP. Он отклоняет дубликаты, небезопасные пути, слишком большие элементы, несовпадающие редакции и контрольные суммы.

**Ограничения:** это черновик для проектирования. Внешние API, платежи и базы не подключаются; сроки и цены не обещаются. Для перехода в реальный Graph Studio требуется отдельное явное действие пользователя и проверка его прав.
