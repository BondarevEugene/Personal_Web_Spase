# Telegram Runtime 2.0 — media, inline callbacks, Outbox

## Возможности

PostgreSQL runtime теперь транзакционно ставит в Outbox четыре команды:
`send_message` (включая `reply_markup.inline_keyboard`),
`send_photo`, `send_document` и `answer_callback_query`.
Callback обновляет тот же диалог под advisory lock, что и текстовое сообщение;
устаревшие кнопки получают alert, не переводя сценарий в новый узел.

Каждая команда перед отправкой проверяется, включая длину подписи,
идентификаторы callback, лимит Telegram callback_data 64 байта и
число команд на update. Worker отправляет их единым Bot API адаптером.
Один update сохраняет состояние, receipt и все outbound-команды атомарно.

## Обязательная миграция

Для **существующей** БД до включения нового runtime применить
`runtime/telegram/migrations/20261122_outbox_media_callback.sql`.
Без миграции CHECK-constraint отклонит новые типы команд, поэтому
переключать сценарии с медиа и inline-кнопками заранее нельзя.
Новая БД, созданная актуальным `postgres_state.DDL`, уже поддерживает методы.

## Эксплуатация

Используйте один webhook и отдельный worker из PR #189 с
`OMNI_RUNTIME_STORAGE=postgresql`, `OMNI_RUNTIME_DATABASE_URL`,
`OMNI_BOT_INSTANCE_ID` и `OMNI_OUTBOX_SEND_ENABLED=1` только для worker.
Состояние `queued` означает запись в Outbox, а не подтверждение Telegram.

**Гарантии:** автоматический повтор неоднозначных отправок запрещён;
оператор должен сверить `claimed` и `needs_reconciliation`.
Exactly-once доставка не гарантируется. При ошибке обработки update
receipt блокируется до ручной сверки.

## Остаётся до production acceptance

- Сквозные тесты с настоящим PostgreSQL, применённой миграцией и реальным
  webhook/worker на Railway.
- Проверка Telegram Bot API на реальном тестовом боте для inline callback,
  фотографий и документов.
- Защита административных метрик и отдельные алерты по зависшим операциям.
- Полноценное управление миграциями и rollback план.

Нельзя считать прохождение unit CI подтверждением реальной доставки.
