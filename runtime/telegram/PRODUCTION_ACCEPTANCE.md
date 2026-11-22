# Telegram Runtime · Production acceptance phase 1

## Что теперь проверяется в CI

Workflow `Telegram PostgreSQL Webhook Contract` запускает настоящий PostgreSQL 16 в
одноразовом контейнере GitHub Actions и выполняет интеграционные тесты.
Они проверяют сохранение receipt и состояния диалога, транзакционный Outbox,
дедупликацию update, последовательную выдачу сообщений, медиа и callback,
запрет отправки следующей команды до подтверждения предыдущей,
карантин неоднозначного исхода и откат транзакции при ошибке сценария.

Тесты не используют реальный Telegram Bot API и не подтверждают доставку в чат.

## Диагностика

В образ добавлен `postgres_diagnostics.py`. Для отдельного Railway worker
можно выполнить:

```sh
python postgres_diagnostics.py --stale-seconds 300
```

Требуются `OMNI_RUNTIME_DATABASE_URL` и `OMNI_BOT_INSTANCE_ID`.
Команда **только читает** агрегированные статусы и число старых записей,
не выводит содержимое сообщений, токены и ID пользователей. Код завершения
0 означает отсутствие неоднозначных статусов; 2 означает необходимость
операторской сверки. Не трактуйте 0 как доказательство доставки.

## Railway

Разделите два сервиса, использующих один Dockerfile и одну Neon PostgreSQL БД:
- **webhook**: команда образа по умолчанию (uvicorn), внешний HTTPS домен,
  Telegram secret header, `OMNI_RUNTIME_STORAGE=postgresql`.
- **outbox worker**: `python outbox_worker.py`, без публичного порта,
  `OMNI_OUTBOX_SEND_ENABLED=1`, те же DB URL, bot instance и BOT_TOKEN.

Примените SQL-миграцию из `migrations/20261122_outbox_media_callback.sql`
до включения новых типов Outbox. Не включайте несколько экземпляров worker
для одного instance до тестирования multi-replica.

При статусе `claimed` или `needs_reconciliation` остановите отправку,
сверьте фактические сообщения в Telegram и журнал, затем решите судьбу
операции вручную. Нельзя без проверки возвращать её в `pending`.

## Что ещё НЕ подтверждено

- Реальная webhook-доставка Telegram -> Railway -> Neon -> Bot API.
- Корректность миграции на существующей production БД.
- Мониторинг доступности worker, оповещения и управление инцидентами через CRM.
- Автоматическое восстановление неопределённых исходов: намеренно запрещено,
  поскольку Telegram Bot API не предоставляет idempotency key.

Не объявлять runtime полностью production-ready до этих проверок.
