# Telegram Delivery Worker · эксплуатационный контракт

## Архитектура

Webhook принимает Telegram update, фиксирует receipt, состояние диалога и команды Outbox в **одной PostgreSQL-транзакции**. Отдельный worker забирает pending-команды и отправляет их через Telegram Bot API. Запускать webhook и worker следует как **два разных сервиса** с одним `OMNI_BOT_INSTANCE_ID` и одной PostgreSQL-базой. В Railway worker использует тот же Docker image, но отдельную start command.

## Конфигурация

Webhook: `OMNI_RUNTIME_STORAGE=postgresql`, `OMNI_RUNTIME_DATABASE_URL`, `OMNI_BOT_INSTANCE_ID`, `BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, `OMNI_SCENARIO_BASE64`.

Worker: те же `OMNI_RUNTIME_DATABASE_URL`, `OMNI_BOT_INSTANCE_ID`, `BOT_TOKEN` плюс явный флаг `OMNI_OUTBOX_SEND_ENABLED=1`.

Команда worker: `python outbox_worker.py --poll-seconds 1 --error-seconds 5` (в контейнере `/app`). Без флага отправка запрещена. **Не запускать** параллельно старый `outbox.py --send-once` на той же очереди без согласованного операционного плана.

## Гарантии и ограничения

* Никакого автоматического повтора после claim: сетевой timeout может означать, что Telegram уже отправил сообщение. Такие команды переходят в `needs_reconciliation`; worker останавливается.
* При падении процесса после claim команда остаётся `claimed`. При старте worker обнаружит это и откажется отправлять новые команды до ручной сверки.
* `pending` означает только постановку в очередь, **не** подтверждённую доставку.
* В текущем PostgreSQL runtime поддерживается только текст; медиа и inline callback требуют отдельного расширения транзакционного протокола. Не включать в продакшене сценарии с неподдерживаемыми узлами.
* Webhook `/outbox/health` показывает агрегированные счётчики без содержимого сообщений; не публикуйте этот endpoint без контроля доступа.
* Из-за отсутствия идемпотентного ключа Telegram Bot API здесь нет гарантии exactly-once.
* Запускайте одну копию worker для данного bot instance, пока не завершено полноценное тестирование нескольких реплик.

## Сверка инцидента

1. Остановить worker и исключить параллельные отправители.
2. Проверить статусы `claimed` и `needs_reconciliation` в `omni_telegram_outbox` для конкретного `bot_instance_id`.
3. Сопоставить фактическое сообщение в Telegram с `update_id` и `seq` по журналу операции. **Не переводить** команду в `pending` только из-за timeout.
4. После доказанного результата оператор отдельно решает, помечать ли как `sent` либо выполнять повторную отправку. Все решения протоколировать.
5. Запустить worker повторно только после устранения неоднозначных статусов.

Для полноценного production rollout остаются: интеграционные испытания с реальным PostgreSQL, webhook end-to-end в Railway, мониторинг worker uptime и контракт для медиа/inline кнопок.
