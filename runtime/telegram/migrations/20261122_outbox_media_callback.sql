-- Apply once to an existing dedicated Telegram runtime PostgreSQL database.
-- New installs use postgres_state.DDL; existing installs must expand the method CHECK.
BEGIN;
ALTER TABLE omni_telegram_outbox
    DROP CONSTRAINT IF EXISTS omni_telegram_outbox_method_check;
ALTER TABLE omni_telegram_outbox
    ADD CONSTRAINT omni_telegram_outbox_method_check
    CHECK (method IN ('send_message','send_photo','send_document','answer_callback_query'));
COMMIT;
