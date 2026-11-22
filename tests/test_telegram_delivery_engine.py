"""No-network tests of the unified transactional Telegram delivery adapter."""
import asyncio
from unittest.mock import AsyncMock

import pytest

from runtime.telegram.outbox import Command, send_command, validate_command
from runtime.telegram.postgres_state import Conversation


def command(method, payload):
    return Command("instance123", 11, 0, 42, method, payload)


@pytest.mark.parametrize(("method", "payload", "api"), [
    ("send_message", {"text": "Hi"}, "send_message"),
    ("send_photo", {"photo": "file-id", "caption": "A"}, "send_photo"),
    ("send_document", {"document": "file-id"}, "send_document"),
    ("answer_callback_query", {"callback_query_id": "cb1"}, "answer_callback_query"),
])
def test_adapter_dispatches(method, payload, api):
    bot = AsyncMock()
    asyncio.run(send_command(bot, command(method, payload)))
    getattr(bot, api).assert_awaited_once()


def test_inline_markup_is_validated_and_dispatched():
    bot = AsyncMock()
    markup = {"inline_keyboard": [[{"text": "Yes", "callback_data": "omni:choose:0"}]]}
    asyncio.run(send_command(bot, command("send_message", {
        "text": "Pick", "reply_markup": markup
    })))
    assert bot.send_message.await_args.kwargs["reply_markup"] == markup


@pytest.mark.parametrize(("method", "payload"), [
    ("send_message", {"text": ""}),
    ("send_photo", {"photo": ""}),
    ("send_document", {"document": "id", "caption": "x" * 1025}),
    ("answer_callback_query", {"callback_query_id": ""}),
    ("delete_message", {"message_id": 1}),
    ("send_message", {"text": "hi", "reply_markup": {"inline_keyboard": [
        [{"text": "A", "callback_data": "x" * 65}]
    ]}}),
])
def test_invalid_commands_fail_closed(method, payload):
    with pytest.raises(ValueError):
        validate_command(command(method, payload))


def test_conversation_action_quota():
    state = Conversation(None, {})
    for _ in range(50):
        state.queue_message(42, "hello")
    with pytest.raises(ValueError):
        state.queue_action(42, "send_photo", {"photo": "file-id"})
