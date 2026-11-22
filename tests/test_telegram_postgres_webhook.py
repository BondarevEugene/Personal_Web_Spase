"""Contract tests for the PostgreSQL transactional webhook interpreter."""
from types import SimpleNamespace

from runtime.telegram.postgres_state import Conversation
from runtime.telegram.postgres_webhook import advance, apply_update, render

SPEC = {
    "start": "greet",
    "nodes": [
        {"id": "greet", "kind": "message", "text": "Hello", "next": "ask"},
        {"id": "ask", "kind": "input", "text": "Your name?", "variable": "name", "next": "choose"},
        {"id": "choose", "kind": "choice", "text": "Pick", "options": [
            {"label": "Yes", "target": "done"}, {"label": "No", "target": "done"}]},
        {"id": "done", "kind": "end", "text": "Thanks {{name}}"},
    ],
}


def event(text):
    return SimpleNamespace(message=SimpleNamespace(
        text=text, chat=SimpleNamespace(id=42),
        from_user=SimpleNamespace(id=7)), callback_query=None)


def test_full_dialogue_queues_without_network_calls():
    state = Conversation(None, {})
    apply_update(SPEC, state, event("/start"))
    assert state.cursor == "ask"
    assert [x["text"] for x in state.outbox] == ["Hello", "Your name?"]
    state.outbox.clear()
    apply_update(SPEC, state, event("Alex"))
    assert state.cursor == "choose"
    assert state.values == {"name": "Alex"}
    assert state.outbox[0]["text"] == "Pick\n1. Yes\n2. No"
    state.outbox.clear()
    apply_update(SPEC, state, event("1"))
    assert state.cursor is None
    assert state.outbox[0]["text"] == "Thanks Alex"


def test_invalid_choice_is_safe_and_does_not_advance():
    state = Conversation("choose", {"name": "Alex"})
    apply_update(SPEC, state, event("99"))
    assert state.cursor == "choose"
    assert state.outbox[0]["text"] == "Выбери номер варианта."


def test_media_queues_transactional_command():
    spec = {"start": "photo", "nodes": [
        {"id": "photo", "kind": "photo", "media": "file-id", "text": ""}]}
    state = Conversation(None, {})
    advance(spec, state, 42, "photo")
    assert state.outbox[0]["method"] == "send_photo"
    assert state.outbox[0]["payload"] == {"photo": "file-id"}


def test_template_does_not_leak_unknown_variables():
    assert render("Hello {{name}} {{secret}}", {"name": "Alex"}) == "Hello Alex "


def test_callback_advances_and_acknowledges():
    state = Conversation("choose", {"name": "Alex"})
    call = SimpleNamespace(id="callback-1", data="omni:choose:0",
                           message=SimpleNamespace(chat=SimpleNamespace(id=42)))
    apply_update(SPEC, state, SimpleNamespace(message=None, callback_query=call))
    assert [action["method"] for action in state.outbox] == [
        "answer_callback_query", "send_message"
    ]
    assert state.outbox[1]["payload"]["text"] == "Thanks Alex"


def test_stale_callback_is_acknowledged_without_advance():
    state = Conversation("choose", {"name": "Alex"})
    call = SimpleNamespace(id="callback-2", data="omni:other:0",
                           message=SimpleNamespace(chat=SimpleNamespace(id=42)))
    apply_update(SPEC, state, SimpleNamespace(message=None, callback_query=call))
    assert state.cursor == "choose"
    assert state.outbox[0]["payload"]["show_alert"] is True
