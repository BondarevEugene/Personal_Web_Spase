"""Persistent Telegram state regression checks (no Telegram network access)."""
from runtime.telegram.state import DialogueStore


def test_dialogue_survives_reopening(tmp_path):
    path = str(tmp_path / "state.db")
    first = DialogueStore(path)
    first.write((101, 202), "question", {"name": "Ірина"})
    first.close()
    second = DialogueStore(path)
    assert second.read((101, 202)) == ("question", {"name": "Ірина"})
    assert second.read((101, 203)) == (None, {})
    second.clear((101, 202))
    assert second.read((101, 202)) == (None, {})
    second.close()


def test_update_claim_is_atomic_and_persistent(tmp_path):
    path = str(tmp_path / "state.db")
    first = DialogueStore(path)
    assert first.claim_update(42) is True
    assert first.claim_update(42) is False
    first.close()
    second = DialogueStore(path)
    assert second.claim_update(42) is False
    second.forget_update(42)
    assert second.claim_update(42) is True
    second.close()
