# OMNIFACTORY · Blueprint handoff v1

## Назначение

Экспорт архитектурного брифа для CRM, Telegram и автоматизации через
`POST /api/v1/blueprint/export`. Это **план**, не созданный проект,
не запись в Neon и не исполняемый workflow.

Контракт: `omnifactory.blueprint.v1`. Поля `saved=false`,
`deployable=false` обязательны. Данные не сохраняются и не логируются
этим endpoint. Проверки вариантов повторно использованы из Blueprint Studio.

## Приёмка

```powershell
python -m ruff check omni_site/blueprint_export.py tests/test_blueprint_export.py
python -m pytest -q tests/test_blueprint_export.py tests/test_public_blueprint_studio.py
```

## До релиза полноценного продукта

Нужна отдельная авторизованная операция импорта в существующую
модель проектов с CSRF, владельцем, миграцией Alembic при необходимости,
проверкой повторного открытия и интеграционными тестами. Нельзя считать
этот экспорт завершённым конструктором или клиентским кабинетом.
